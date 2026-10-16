# Pardes Guard

**You don't need a middleman.** Pardes Guard is a free phone web app for people going abroad for the
first time for work or study, and for their families. It shows every step of the journey, what each
step should really cost, and checks an agent and their papers for warning signs before anyone pays.
If something goes wrong abroad, it helps the person write letters they send themselves and keeps
their evidence safe.

Live link: not deployed yet. It goes here after `firebase deploy` (see [Put it online](#put-it-online)).

It is built for a first-time traveller on a cheap Android phone and a weak connection: Urdu and
English, with Hindi, Bengali, Nepali and Filipino drafted by machine; voice in and out; plain words;
a simple mode; and a kit that keeps the key screens on the phone for when the internet is gone.

## What it does

| Screen | What it does |
|---|---|
| Journey | Three questions (why, from, to) build a personal plan from the country packs: documents, visa steps, departure and arrival. Each step says who does it, where to go, its official link and whether our team has checked it. Stages are passport pages that get stamped. |
| Check | Photos, PDFs or a voice note of an offer letter, contract, visa or admission letter. Gemini reads them; fixed rules decide. Red STOP, amber CHECK or green LOOKS OK, with every reason, its evidence and its source, and next steps. Hidden instructions aimed at AI readers are caught. With the AI off, a typed form gives the same rules-based result. Four fictional samples to try. |
| Agents | Search the licensed list (a fictional sample until an admin imports the official one), see a licence's status and staff warnings, rate an agent, report one. |
| Real cost | Each official cost of the route, with a number only when it has a source and a checked date, compared with what the agent asks. |
| Readiness scan | Reads the name and expiry from each paper (the photos are not kept), checks months left on the passport and the name spelling across papers. |
| Cases | Wage, passport or fraud problems as a ladder of letters (employer, embassy, legal aid or regulator). The person edits, approves and sends each letter from their own WhatsApp or email. Nothing is sent by the app. |
| Wage check | Short or late pay against the contract, then a case in one tap. |
| Evidence vault | Files stay on the phone; each gets a SHA-256 fingerprint chained to the one before, and everything downloads as a ZIP with a manifest. |
| Family view | A 14-character code shows a case's progress to family, never its letters or files. |
| SOS | Quick exit to a blank page, help contacts from the packs, a WhatsApp message to send yourself, an emergency case. |
| Eligibility | What a person writes, compared by code with each route's listed requirements, with the reason for every line. Never "you are eligible". |
| Important dates | The passport date, each case's next step and the person's own dates, each with a Google Calendar link. |
| Assistant | Questions answered by Gemini through five read-only functions over the app's own data, by typing or by voice. Links under each answer come from the data, never from the model. |
| Interview practice | A voice (Gemini Live) or typed practice interview built from the route's own topics, with per-topic feedback labelled practice. |
| NGO console | Staff review worker reports, see agents linked by shared phones or fee accounts, publish warnings that every check then uses, and confirm fake document layouts. Anyone can try it with sample data on their own phone. |
| Admin | An admin imports the official licensed list from a CSV file, after a preview, and every agent check uses it. |
| Privacy | A plain page on what is kept and where, the AI answer language, sharing warnings (opt-in), and "Delete everything". |

Country packs ship for Pakistan and the Philippines (origin) and Saudi Arabia, UAE, Qatar, Japan,
South Korea, Canada, the UK and Australia (destination). **All of their content is marked draft** until
the team checks it against the official page linked on each item.

## How it is built ($0)

```
 Phone browser
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  Static Next.js site (one folder of pages per language)                   │
 │  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐ │
 │  │ Rule engine  │  │ Country packs │  │ LocalStore   │  │ Service      │ │
 │  │ (TypeScript, │  │ (JSON, loaded │  │ (guests)     │  │ worker       │ │
 │  │  tested)     │  │  per country) │  │ IndexedDB    │  │ (offline kit)│ │
 │  └──────────────┘  └───────────────┘  │ (vault files)│  └──────────────┘ │
 │                                       └──────────────┘                    │
 └────────┬───────────────────┬────────────────────────┬────────────────────┘
          │                   │                        │
   Firebase Hosting    Firebase Auth +          Firebase AI Logic
   (static files,      Cloud Firestore          (Gemini Developer API)
    headers)           (accounts, rules)        gemini-3.8-flash → 3.5-flash-lite → gemma-4-31b-it
                                                Gemini Live: gemini-3.1-flash-live-preview
```

One rule shapes the design: **decisions are code, words are Gemini.** Verdicts, risk scores, fees,
eligibility, wage arithmetic and case timing come from deterministic, tested code. Gemini reads
papers and voice notes into structured data, explains results in the person's language, drafts
letters, answers questions through the app's own functions, and runs interview practice. When Gemini
is unavailable or out of free quota, the app keeps working with rules only and template letters.

The live demo runs entirely on Firebase's no-cost plan, with Gemini through Firebase AI Logic. The production design, with ADK agents on Cloud Run, Cloud KMS-signed evidence, Sensitive Data Protection, Model Armor and a Spanner Graph fraud network, is implemented in the repository with unit tests and deployment scripts.

The production backend in `backend/` has not been run against live Google services.

Choices worth knowing (all of them, with reasons, are in [`DECISIONS.md`](DECISIONS.md)):

- Uploaded papers are untrusted. They go to Gemini wrapped as data, every answer is screened for
  injected instructions, and a hit becomes a visible flag.
- Phone and account numbers keep only their last four digits in checks, cases and letters. Fraud
  signals are hashed on the phone before they are shared, and only when the person opts in.
- No case escalates on its own: the ladder moves when the app opens, and each letter waits for the
  person's approval and is sent from their own apps.
- Staff are named only in `roles/{uid}`, which the client cannot write; `firestore.rules` checks it on
  every staff read and write.
- Files in the vault never leave the phone (the free plan has no file storage); only their records do.

## Google tools used

| Tool | Used for |
|---|---|
| Firebase Hosting | The static site, security headers |
| Firebase Authentication | Google sign-in (guests use the app without an account) |
| Cloud Firestore | Accounts' journeys, checks, cases, evidence records, shares, reports, signals, published warnings |
| Firebase AI Logic with the Gemini Developer API | Reading papers and voice notes (JSON schemas), explanations, translations, letters, the assistant (function calling), interview feedback |
| Gemini Live API (preview) | Talking to the assistant and interview practice, with transcripts |
| Gemma (`gemma-4-31b-it`) | Last model in the reading fallback chain |
| Google Calendar template links | Saving important dates, filled in, by the person |
| Google Search and Maps links | Looking up an employer named on a paper (plain links; grounding is off on the free tier) |
| Google Fonts | Atkinson Hyperlegible Next, Noto Nastaliq Urdu, Noto Naskh Arabic, Noto Sans Devanagari, Bengali, Sinhala and Tamil, served from the site |
| Production design (`backend/`, not deployed) | Agent Development Kit, Cloud Run, Cloud KMS, Sensitive Data Protection, Model Armor, Spanner Graph, Cloud Scheduler |

## Run it on your computer

You need Node 22 (`node -v` should print `v22...`). Nothing else is needed to try the app.

Unzip a new version into an empty folder, never over an older copy: files the new version no longer
has would stay behind and break the build. `npm run dev` and `npm run build` check for them first and
name them; `node scripts/check-stale.mjs --fix` (in `frontend/`) deletes them.

```bash
cd frontend
npm ci                 # installs exactly the versions in package-lock.json
npm run dev            # open http://localhost:3000
```

With no Firebase values the app runs fully on the device: no sign-in, data stays in the browser, no
Gemini (each AI screen says so and offers its typed or rules-only path). The browser tests run this way.

To see the built site the way Firebase Hosting serves it, offline kit included:

```bash
npm run build          # static site in frontend/out
npm run preview        # open http://localhost:4173
```

## Settings files

Three places hold settings. Only the first is needed for the live app.

| Where | Needed for | What goes in it |
|---|---|---|
| `frontend/.env.local` | The live app (Firebase) | The four Firebase web app values (step 4 below). Copy it from `frontend/.env.example`. |
| `backend/.env` | The API on your computer only | `LLM_BACKEND=auto` and a `GEMINI_API_KEY` from Google AI Studio; the rest can stay as in `backend/.env.example`. |
| Cloud Run | The deployed API | Nothing to type. `infra/deploy.sh` sets every value; Gemini, Firestore, Spanner and KMS use the service account (no keys); the two secrets are made by `infra/setup.sh` in Secret Manager. |

The AI switches by itself in both builds. The live app tries Gemini through Firebase AI Logic and,
when it is out of quota, unreachable or not set up, says so and carries on with the rules and the
typed form. The API does the same with `LLM_BACKEND=auto`: a paper Gemini could not read is marked
"could not be read just now", so its result is never green, and Gemini is tried again after
`AI_COOLDOWN_SECONDS`. `LLM_BACKEND=fake` is only for the tests.

What the live app uses from Firebase: Hosting, Authentication (Google sign-in; guests need no
account), Firestore and AI Logic, all within the free quotas. It was built for the Spark plan, so it
uses no Cloud Storage (vault files stay on the phone), no Cloud Functions (case steps move when the app
opens) and no phone number (SMS) sign-in. The project is now on Blaze because billing is linked for
the API on Cloud Run.

## Put it online

Follow the steps in order. The live app stays within Firebase's free quotas.

**1. Tools on your computer.** Node 22, then the Firebase CLI, then sign in:

```bash
npm install -g firebase-tools
firebase login
```

**2. Billing.** The team's Firebase project is `pardes-ea3e1`. It has billing linked for the API on
Cloud Run, so the console shows "Blaze": keep it that way, and set the budget alert in
[`infra/CLOUD_RUN.md`](infra/CLOUD_RUN.md) (step 2) before deploying anything.

**3. Switch on the Firebase services** at https://console.firebase.google.com:

- Open the project `pardes-ea3e1` (it exists already, with its web app registered).
- Authentication > Get started > Sign-in method > Google > Enable > choose a support email > Save.
- Firestore Database > Create database > pick a location near the users (for example `asia-south1`,
  Mumbai; it cannot be changed later) > Start in production mode. The real rules are deployed in step 6.
- AI Logic (left menu) > Get started > choose the **Gemini Developer API**.
- Project settings (gear icon) > General > Your apps > Add app > Web (`</>`) > any nickname > Register.

**4. Paste the web app's config.** Project settings > General > Your apps > your web app > SDK setup
and configuration > Config shows an object like `{ apiKey: "...", authDomain: "...", ... }`. Copy four
of its values into a new file `frontend/.env.local` (start from the example):

```bash
cd frontend
cp .env.example .env.local
```

| In the console's config | Line in `frontend/.env.local` |
|---|---|
| `apiKey` | `NEXT_PUBLIC_FIREBASE_API_KEY=` |
| `authDomain` | `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=` |
| `projectId` | `NEXT_PUBLIC_FIREBASE_PROJECT_ID=` |
| `appId` | `NEXT_PUBLIC_FIREBASE_APP_ID=` |

Leave `NEXT_PUBLIC_GROUNDING=off`. These values are public by design (they end up in the page);
`.env.local` is git-ignored anyway. Never put a service-account key anywhere in this repository. Do
not add website (HTTP referrer) restrictions to this API key: the site sends no `Referer` header
(`Referrer-Policy: no-referrer` in `firebase.json`), so a key restricted that way refuses every request.

**5. Point the CLI at the project** (once, from the repository root). This writes `.firebaserc`, which
git ignores:

```bash
firebase use --add      # pick pardes-ea3e1, and give it the alias "default"
```

(Or copy `.firebaserc.example` to `.firebaserc` and put the project id in it.)

**6. Build and deploy** (from the repository root):

```bash
cd frontend && npm ci && npm run build && cd ..
firebase deploy --only hosting,firestore:rules
```

The command prints the live link (`https://<project id>.web.app`). Put it at the top of this README.
The values in `.env.local` are built into the site, so after changing them, build and deploy again.

**7. Make yourself staff.** Open the live link and sign in once (More > Sign in > Google). Then, in
the Firebase console:

1. Authentication > Users: copy your User UID.
2. Firestore Database > Start collection. Collection ID: `roles`. Document ID: paste the UID.
3. Add a field named `role`, type string, value `admin`. Save.

Reload the app: More > Staff now opens the NGO console and Admin (the Staff section is hidden in
simple mode). Other NGO staff get the value `ngo`: they review reports and publish warnings, and only
an admin can replace the licensed list.

**8. Check that it works on the live link.** These have never run against Google, so this is the first
real test of each:

- [ ] More > Sign in > Google: you are signed in, and your journey is still there. Then sign out.
  This is the first thing to check: `firebase.json` sends `X-Frame-Options: DENY` on every page, and
  whether that also reaches Firebase's own sign-in helper pages (`/__/auth/...`) has not been tested.
  If the Google window closes at once or the console mentions a frame, delete the `X-Frame-Options`
  entry from `firebase.json` and run `firebase deploy --only hosting` again.
- [ ] Check > one of the samples: the result says AI read the paper and the stamp lands.
- [ ] Check > a photo of a printed test paper of your own (never a real person's document).
- [ ] Assistant: type a question about Saudi Arabia; links appear under the answer.
- [ ] Assistant > talk (allow the microphone): it answers out loud and the words appear on screen.
- [ ] Interview practice as Ayesha (UK student visa), by voice and by typing, then the feedback.
- [ ] A case: draft the letter with AI, approve it, open it in WhatsApp.
- [ ] Family view: share a case's code and open it in another browser without signing in.
- [ ] NGO console and Admin open for your account, and not for an account without a role.
- [ ] More > Save for use without internet, then airplane mode: Home, SOS and Cases still open.
- [ ] All of the above once on a cheap Android phone, in Urdu.

When something fails, note the screen, what you tapped, and any red message in the browser's console
(desktop Chrome: right-click > Inspect > Console).

## The production API on Cloud Run (optional, uses billing)

With billing on the project, the backend runs on Cloud Run with the real services it was written for:
Gemini on Gemini Enterprise Agent Platform, Firestore, a Spanner Graph free trial instance, Cloud KMS,
Sensitive Data Protection, Model Armor, Secret Manager and Cloud Scheduler. Everything is done from
Cloud Shell with two scripts, then checked end to end with `backend/app/scripts/live_check.py`, which
writes `backend/LIVE_CHECK.md`. Steps, costs and how to take it down: [`infra/CLOUD_RUN.md`](infra/CLOUD_RUN.md).

Until `backend/LIVE_CHECK.md` exists and passes, say nothing more in the deck than the sentence in
[How it is built](#how-it-is-built-0).

## What is left, and where it goes

The app works with what it has. These items need people, accounts or official pages that the build
environment did not have. The owner column follows the team table below.

| # | What is missing | Where to get it | Where it goes | Owner |
|---|---|---|---|---|
| 1 | Firebase services and web config | Firebase console (steps 3 and 4 above) | `frontend/.env.local` | Ahsaan |
| 2 | First deploy and the live link | `firebase deploy` (step 6) | Top of this README | Ahsaan |
| 3 | Staff accounts | Each person's User UID: Authentication > Users | Firestore: `roles/{uid}` with `role: admin` or `ngo` (step 7) | Ahsaan |
| 4 | The official list of licensed overseas employment promoters | Bureau of Emigration & Overseas Employment (the Pakistan pack lists `beoe.gov.pk`) | App: More > Staff > Admin > CSV file. See [The licensed list](#the-licensed-list) | Rimsha |
| 5 | Checked content for Ahmed's route (Pakistan to Saudi Arabia) | Official pages only | `backend/app/packs/data/PK.yaml` and `SA.yaml`. See [Country packs](#country-packs) | Rimsha |
| 6 | Checked content for Ayesha's route (Pakistan to the UK) | Official pages only | `backend/app/packs/data/PK.yaml` and `GB.yaml` | Rimsha |
| 7 | A native reader for each language | People who speak it | `frontend/lib/i18n/locales/`. See [Languages](#languages) | Muneeb |
| 8 | The Firestore rules tests | A computer with Java (JDK 11 or newer) | `cd frontend && npm run test:rules` | Ahsaan |
| 9 | A real phone test | A cheap Android phone | The checklist in step 8 | Muneeb |
| 10 | Deck and demo video | | Outside this repository; use the wording in [How it is built](#how-it-is-built-0) | Muneeb |
| 11 | The production API with real Google services (optional; the live app does not use it) | Cloud Shell in `pardes-ea3e1`, which now has billing | [`infra/CLOUD_RUN.md`](infra/CLOUD_RUN.md); the result in `backend/LIVE_CHECK.md` | Ahsaan |
| 12 | App Check (optional) | Firebase console > App Check | Confirm it stays free before turning it on; the code does not use it yet | Ahsaan |

Not built, because no pack has an official source for them: the visa form guide and official register
links for admission letters (see `DECISIONS.md`, entry 95).

### Country packs

All content lives in `backend/app/packs/data/<country>.yaml`; the web app gets a copy. Every pack is
`status: draft`. Each file starts with how to check an item; in short:

1. Read the official page. Never fill a fee, office, phone number, link or rule from memory or from an
   agent. An empty field makes the app say "not added yet", which is safe.
2. A link is accepted only when its domain is in that pack's `official_domains`. Add the domain first,
   only after checking it is the real official site.
3. Fill the fields, add the page under `sources`, set `status: verified` and `last_verified: YYYY-MM-DD`.
   A verified item without a source and a date stops the export. Put the Urdu beside it under `i18n.ur`.

What is empty today:

| Field | File | Shape |
|---|---|---|
| Legal maximum recruitment fee | `PK.yaml` | `max_recruitment_fee: { amount: <number>, currency: PKR, period: once }` and `max_recruitment_fee_source: { title: <page title>, url: <official link> }` |
| Each document guide (passport, CNIC, police certificate, attestations, medical, Protector) | `PK.yaml` > `documents` | `online_or_office` (online, office or both), `steps`, `bring`, `typical_time`, `official_url`, `sources` |
| Each cost of a route | `SA.yaml` and `GB.yaml` > `visa_routes` > `fees` | `amount`, `currency`, `source: { title, url }`, `last_verified`, and `paid_by` (worker, employer, recruiter, government or university) only when the page says who pays |
| Help contacts shown on SOS | `SA.yaml` and `GB.yaml` | `complaint_channels` and `embassy_contacts`, each `{ name, url, description }` |
| Passport months required | `SA.yaml` > `sa-passport`; `GB.yaml` has no passport requirement yet (add one with `kind: passport` under the route's `requirements`) | `rule: { type: range, field: passport_valid_months, min: <months> }` (the comment in `SA.yaml` shows where) |
| Interview topics for other routes | the route in its destination pack | `interview_topics: [ ... ]`, only from an official source |

Then export the packs into the web app, test, and deploy again:

```bash
python3 -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cd frontend && npm run data && npm test && npm run build && cd ..
firebase deploy --only hosting
```

On Windows, if `npm run data` cannot find `python3`, run `python frontend/scripts/export_data.py` from
the repository root instead. Some tests check today's draft content (for example, the cost screen test
expects Pakistan's legal maximum fee to say "not added yet", and the check test expects the "Some
rules used here are drafts" line). When verified content changes a result, update
the test's expected result to match the content, never the content to match the test.

### The licensed list

The agent search and every check use a fictional sample list until the official one is imported. The
file is a CSV with a header row:

```
license_no,name,status,city,list_date
ABC1234LHR,"Example Overseas Employment Promoters, Lahore",active,Lahore,2026-10-01
```

`license_no`, `name` and `status` (active, suspended or cancelled) are required; names with commas go
in quotes; the file must be under 2 MB. The example row above is made up. If the regulator publishes
the list as a PDF or a web page, turn it into this CSV and check a few rows by hand against the official
page; the app cannot tell whether a file is official.

- On the live site (no rebuild): More > Staff > Admin > CSV file > check the preview > set the list
  date > Use this list. "Go back to the sample list" undoes it.
- Or built into the site: `python frontend/scripts/export_data.py --recruiters path/to/list.csv`, then
  build and deploy. Pass `--recruiters` on every export, or the sample comes back.

### Languages

| Language | File | State |
|---|---|---|
| English | `frontend/lib/i18n/locales/en.ts` | Complete |
| Urdu | `frontend/lib/i18n/locales/ur.ts` | Complete, needs a native read |
| Hindi, Bengali, Nepali, Filipino | `hi.ts`, `bn.ts`, `ne.ts`, `fil.ts` | Drafted by machine, labelled so on every screen. Open questions for each reviewer are in `frontend/lib/i18n/review/`. |

The staff screens (NGO console, Admin) are in English and Urdu only. After a native speaker has
corrected one of the drafted languages, remove it from `MACHINE_LOCALES` in
`frontend/lib/i18n/config.ts` so the machine-translation line goes away, then run `npm test`.

If Google renames or retires a Gemini model, the names are in `frontend/lib/ai.ts` (reading, letters,
assistant) and `frontend/lib/live.ts` (voice).

## Tests

```bash
cd frontend
npm run typecheck
npm test               # unit tests (vitest): engine, store, AI fallbacks, letters, assistant, i18n
npm run build
npx playwright install --with-deps chromium     # once, on a new computer
npm run test:e2e       # Playwright on the built site: both hero stories, every screen,
                       # axe accessibility checks, text at 200%, keyboard only, offline kit
npm run test:rules     # Firestore rules against the emulator (needs Java)

cd ../backend && python -m pytest -q     # the production design's tests
```

The browser tests expect a build without Firebase values. Rename `frontend/.env.local` before
`npm run build` and `npm run test:e2e`, and put it back before the next deploy build.

Last run on 14 October 2026 (see the report in `DECISIONS.md` for what was not run): 356 unit
tests, 294 browser tests and 82 backend tests passed. The Firestore rules tests were not run (the
emulator could not be downloaded in the build environment).

## What has been verified, and what has not

Verified here, on the built site in headless Chromium at phone size: both hero stories end to end,
every screen in English and Urdu (light and dark) with no serious axe finding, the busiest screens in
the four machine-drafted languages, text at 200% with no sideways scrolling, keyboard-only use, the
offline kit with the server stopped, the NGO warning reaching a worker's check, and an imported
licensed list reaching the agent search.

Not run against Google yet: any Gemini or Gemini Live call, Google sign-in, Firestore and its rules,
and a real phone (fonts, voices, microphone, camera). The AI screens were checked only in a build with
placeholder Firebase values, where every call fails with the "could not reach" message.

Content to check before real people use it: every country pack item (all draft), the recruiter list
(a fictional sample until an admin imports the official CSV), Pakistan's legal maximum recruitment fee,
help contacts for Saudi Arabia and the UK, and a native speaker's read of every language. Pardes
Guard flags warning signs; it cannot prove a paper is genuine and does not give legal advice.

## Demo script (under 3 minutes)

1. Choose Urdu. Three questions: work, Pakistan, Saudi Arabia. Home shows the next step as a
   boarding pass.
2. Check the agent's offer letter (sample): the red stamp lands. Show the reasons with sources: lower
   pay than promised, the passport kept, a licence that belongs to another firm.
3. Open a case from the result; edit and approve the letter; send it from WhatsApp. Share the family
   code and open the family view.
4. NGO console: two reports name agencies with the same phone number; publish the warning. Check the
   same paper again: the warning is now on it.
5. Switch to Ayesha (UK student visa): her journey, the readiness scan, the interview topics, and a
   question to the assistant by voice.
6. Close on what is verified and what the team checks next.

## Team

| Person | Owns |
|---|---|
| Ahsaan | API, ADK agents, case engine, evidence chain, integrity network, A2A, deployment |
| Rimsha | Gemini prompts and reading quality, red-team run with Gemini, country pack verification |
| Muneeb | Web app, Urdu copy, accessibility, demo video, deck |

## Repository layout

```
frontend/   the app: Next.js static export, rule engine (lib/engine), stores, AI providers,
            country packs (data/), dictionaries (lib/i18n/locales), unit and browser tests
backend/    the production design: FastAPI, ADK agents, services, packs, tests (not deployed)
infra/      Cloud Run setup and deploy scripts, Cloud Build, Spanner schema (production design)
firestore.rules, firebase.json   the $0 build's rules and hosting
DECISIONS.md                     what was decided, and what has not been tested
frontend/DESIGN.md               the design system
```
