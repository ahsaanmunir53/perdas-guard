#!/usr/bin/env bash
# One-time setup of a Google Cloud project for Pardes Guard.
#
#   PROJECT_ID=my-project ./infra/setup.sh
#   PROJECT_ID=my-project WITH_SPANNER=1 ./infra/setup.sh     # also create the Spanner Graph database
#
# Safe to re-run: resources that already exist are left as they are.
# Two steps stay manual (console): enable the Phone sign-in provider in Firebase Authentication, and
# create a Model Armor template if you want MODEL_ARMOR_TEMPLATE set. See README.md.

set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
REGION="${REGION:-asia-south1}"
BUCKET="${BUCKET:-${PROJECT_ID}-pardes-evidence}"
API_SA="pardes-api@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_SA="scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com"

exists() { "$@" >/dev/null 2>&1; }

gcloud config set project "$PROJECT_ID" >/dev/null

echo "== Enabling APIs"
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  firestore.googleapis.com storage.googleapis.com cloudkms.googleapis.com secretmanager.googleapis.com \
  cloudscheduler.googleapis.com aiplatform.googleapis.com dlp.googleapis.com modelarmor.googleapis.com \
  firebase.googleapis.com identitytoolkit.googleapis.com logging.googleapis.com

echo "== Artifact Registry"
exists gcloud artifacts repositories describe pardes --location="$REGION" ||
  gcloud artifacts repositories create pardes --repository-format=docker --location="$REGION"

echo "== Service accounts"
exists gcloud iam service-accounts describe "$API_SA" ||
  gcloud iam service-accounts create pardes-api --display-name="Pardes Guard API"
exists gcloud iam service-accounts describe "$SCHED_SA" ||
  gcloud iam service-accounts create scheduler-invoker --display-name="Pardes Guard case timer"

for role in roles/datastore.user roles/aiplatform.user roles/dlp.user roles/modelarmor.user roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${API_SA}" --role="$role" \
    --condition=None >/dev/null
done

echo "== Firestore (Native mode)"
exists gcloud firestore databases describe --database="(default)" ||
  gcloud firestore databases create --location="$REGION"

echo "== Evidence bucket (private)"
exists gcloud storage buckets describe "gs://${BUCKET}" ||
  gcloud storage buckets create "gs://${BUCKET}" --location="$REGION" \
    --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${API_SA}" --role=roles/storage.objectAdmin >/dev/null

echo "== Cloud KMS key for signing the evidence chain"
exists gcloud kms keyrings describe pardes --location="$REGION" ||
  gcloud kms keyrings create pardes --location="$REGION"
exists gcloud kms keys describe evidence-signing --keyring=pardes --location="$REGION" ||
  gcloud kms keys create evidence-signing --keyring=pardes --location="$REGION" \
    --purpose=asymmetric-signing --default-algorithm=ec-sign-p256-sha256
for role in roles/cloudkms.signerVerifier roles/cloudkms.publicKeyViewer; do
  gcloud kms keys add-iam-policy-binding evidence-signing --keyring=pardes --location="$REGION" \
    --member="serviceAccount:${API_SA}" --role="$role" >/dev/null
done

echo "== Secrets (random values, never printed)"
for secret in pardes-hash-salt pardes-evidence-key; do
  if ! exists gcloud secrets describe "$secret"; then
    openssl rand -base64 48 | tr -d '\n' | gcloud secrets create "$secret" --replication-policy=automatic --data-file=-
  fi
  gcloud secrets add-iam-policy-binding "$secret" --member="serviceAccount:${API_SA}" \
    --role=roles/secretmanager.secretAccessor >/dev/null
done

if [[ "${WITH_SPANNER:-0}" == "1" ]]; then
  echo "== Spanner Graph (integrity network)"
  gcloud services enable spanner.googleapis.com
  exists gcloud spanner instances describe pardes ||
    # Spanner Graph needs the Enterprise (or Enterprise Plus) edition.
    gcloud spanner instances create pardes --config="regional-${REGION}" --processing-units=100 \
      --edition=ENTERPRISE --description="Pardes Guard integrity network"
  exists gcloud spanner databases describe integrity --instance=pardes ||
    gcloud spanner databases create integrity --instance=pardes --ddl-file="$(dirname "$0")/spanner/schema.sql"
  gcloud spanner databases add-iam-policy-binding integrity --instance=pardes \
    --member="serviceAccount:${API_SA}" --role=roles/spanner.databaseUser >/dev/null
fi

echo
echo "Done. Next:"
echo "  1. Firebase console: add this project, enable Authentication > Phone, register a web app."
echo "  2. Fill frontend/.env.production from the web app's config (see frontend/.env.example)."
echo "  3. PROJECT_ID=${PROJECT_ID} ./infra/deploy.sh"
