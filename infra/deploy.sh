#!/usr/bin/env bash
# Build and deploy Pardes Guard: API on Cloud Run, the hourly case timer, and the web app on Firebase Hosting.
#
#   PROJECT_ID=my-project ./infra/deploy.sh
#   PROJECT_ID=my-project WITH_SPANNER=1 WITH_A2A=1 ./infra/deploy.sh
#
# Run infra/setup.sh once first. Requires gcloud, node 20+, and the Firebase CLI (npx firebase-tools works).

set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
REGION="${REGION:-asia-south1}"
BUCKET="${BUCKET:-${PROJECT_ID}-pardes-evidence}"
SERVICE="pardes-guard-api"
API_SA="pardes-api@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_SA="scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com"
TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/pardes/api:${TAG}"
KMS_KEY_VERSION="projects/${PROJECT_ID}/locations/${REGION}/keyRings/pardes/cryptoKeys/evidence-signing/cryptoKeyVersions/1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

gcloud config set project "$PROJECT_ID" >/dev/null

echo "== Tests"
(cd "$ROOT/backend" && python3 -m pytest -q)

echo "== Building ${IMAGE}"
gcloud builds submit "$ROOT/backend" --tag "$IMAGE"

# "^@^" switches gcloud's list separator to @ so values may contain commas.
ENV_VARS="^@^ENV=prod@LLM_BACKEND=gemini@GOOGLE_CLOUD_PROJECT=${PROJECT_ID}@GOOGLE_CLOUD_LOCATION=global"
ENV_VARS+="@GOOGLE_GENAI_USE_ENTERPRISE=true@STORE_BACKEND=firestore@AUTH_MODE=firebase@GCS_BUCKET=${BUCKET}"
ENV_VARS+="@KMS_KEY_VERSION=${KMS_KEY_VERSION}@USE_SENSITIVE_DATA_PROTECTION=true"
ENV_VARS+="@CORS_ORIGINS=[\"https://${PROJECT_ID}.web.app\",\"https://${PROJECT_ID}.firebaseapp.com\"]"
if [[ -n "${MODEL_ARMOR_TEMPLATE:-}" ]]; then ENV_VARS+="@MODEL_ARMOR_TEMPLATE=${MODEL_ARMOR_TEMPLATE}"; fi
if [[ "${WITH_SPANNER:-0}" == "1" ]]; then ENV_VARS+="@GRAPH_BACKEND=spanner@SPANNER_INSTANCE=pardes@SPANNER_DATABASE=integrity"; fi
if [[ -n "${PARTNER_AGENT_CARD_URL:-}" ]]; then ENV_VARS+="@PARTNER_AGENT_CARD_URL=${PARTNER_AGENT_CARD_URL}"; fi

echo "== Deploying ${SERVICE}"
# Public at the network level so Firebase Hosting can reach it; every endpoint checks the
# Firebase ID token (or the scheduler's OIDC token) itself.
gcloud run deploy "$SERVICE" --image "$IMAGE" --region "$REGION" \
  --service-account "$API_SA" --allow-unauthenticated \
  --cpu 1 --memory 1Gi --concurrency 40 --timeout 120 --min-instances 0 --max-instances 10 \
  --set-env-vars "$ENV_VARS" \
  --set-secrets "HASH_SALT=pardes-hash-salt:latest,EVIDENCE_SIGNING_KEY=pardes-evidence-key:latest"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
gcloud run services update "$SERVICE" --region "$REGION" \
  --update-env-vars "SCHEDULER_AUDIENCE=${URL},SCHEDULER_SERVICE_ACCOUNT=${SCHED_SA}" >/dev/null

echo "== Case timer (Cloud Scheduler, hourly, OIDC)"
JOB_ARGS=(--location "$REGION" --schedule "0 * * * *" --uri "${URL}/api/cases/tick" --http-method POST
  --oidc-service-account-email "$SCHED_SA" --oidc-token-audience "$URL")
if gcloud scheduler jobs describe pardes-case-tick --location "$REGION" >/dev/null 2>&1; then
  gcloud scheduler jobs update http pardes-case-tick "${JOB_ARGS[@]}"
else
  gcloud scheduler jobs create http pardes-case-tick "${JOB_ARGS[@]}"
fi

if [[ "${WITH_A2A:-0}" == "1" ]]; then
  echo "== Public A2A agent (separate service, same image)"
  A2A_SERVICE="pardes-guard-a2a"
  gcloud run deploy "$A2A_SERVICE" --image "$IMAGE" --region "$REGION" \
    --service-account "$API_SA" --allow-unauthenticated --memory 1Gi \
    --command uvicorn --args "app.a2a_server:app,--host,0.0.0.0,--port,8080" \
    --set-env-vars "$ENV_VARS" \
    --set-secrets "HASH_SALT=pardes-hash-salt:latest,EVIDENCE_SIGNING_KEY=pardes-evidence-key:latest"
  A2A_URL="$(gcloud run services describe "$A2A_SERVICE" --region "$REGION" --format='value(status.url)')"
  gcloud run services update "$A2A_SERVICE" --region "$REGION" --update-env-vars "A2A_PUBLIC_URL=${A2A_URL}" >/dev/null
  echo "A2A agent card: ${A2A_URL}/.well-known/agent-card.json"
fi

echo "== Web app"
if [[ ! -f "$ROOT/frontend/.env.production" ]]; then
  echo "frontend/.env.production is missing: copy frontend/.env.example and fill in the Firebase web config." >&2
  exit 1
fi
# Next.js lets .env.local override .env.production, which would ship localhost and demo sign-in.
if [[ -f "$ROOT/frontend/.env.local" ]]; then
  echo "frontend/.env.local exists and would override .env.production. Move it aside and run again." >&2
  exit 1
fi
(cd "$ROOT/frontend" && npm ci && npm run build)
(cd "$ROOT" && npx --yes firebase-tools deploy --only hosting,firestore:rules --project "$PROJECT_ID")

echo
echo "API: ${URL}"
echo "App: https://${PROJECT_ID}.web.app"
