# Pardes Guard: build brief

You are building Pardes Guard for the Google Cloud AI Builder Cup 2026 (Hack2skill). Read this whole file before you write any code. The attached `pardes-guard.zip` is the current repository; this file is also at its root.

## 0. How you work

- Be honest about state. Never say something works, passes or is deployed unless you ran it and saw it. If you could not test something (a live Google service, a real phone), say so plainly in your report.
- Never invent facts that end up in the app: official URLs, office names, fees, phone numbers, visa rules, laws. If the repo data or the team does not give it to you, leave the field empty with status `draft` and a `TODO(source)` note. A wrong fee or helpline in this app can cost a worker their savings.
- Never commit secrets. The Firebase web config goes in `frontend/.env.local` (git-ignored). No service-account keys anywhere.
- Work in the phases in section 12. At the end of each phase: run typecheck, tests and build, take screenshots, and send a short report (what works, what does not, what you could not test). Then continue.
- Ask the team only when the choice is theirs (scope, content, account setup). Otherwise decide, and record the decision in `DECISIONS.md`.
- Deadline: submission closes 18 October 2026. Everything in P1 must work end to end by the end of 17 October. 18 October is for fixes, the video and the deck only. No new features that day.

## 1. The competition and what wins

- Judging: Technical 40%, Impact 25%, Innovation 25%, UX 10%. Special prize: "Best use of Google Cloud AI tools".
- Submission: a deployed link, a public GitHub repo, a video under 3 minutes and a PDF deck, all in English.
- Track: Sustainability & Social Impact.
- Hard constraints: Gemini must be used, and the app is deployed on Firebase. The team has no billing account, so everything must run on Firebase's no-cost Spark plan and the Gemini Developer API free tier. Nothing may need a card.
- What moves the score: a link that works the moment a judge opens it; one complete story that runs end to end; AI used where it clearly helps and plain code where code is better; and a UI that feels made for these users, not a template.

## 2. The product

**Who it is for.** People going abroad for the first time for work or study, mostly from Pakistan, India, Bangladesh, Nepal, Sri Lanka, the Philippines and Indonesia, and their families. Many have little schooling, read Urdu or another non-English language, use a cheap Android phone on a weak connection, and have never dealt with a visa. Secondary users: NGO and legal-aid staff, and an admin who keeps the content correct.

**The problem.** The process is confusing, so people pay local agents and brokers to handle documents, visas and tickets. Many agents overcharge, use borrowed or fake licences, hand over fake visas or contracts, or keep passports. Once abroad, workers face unpaid wages and do not know whom to contact.

**The promise: "You don't need a middleman."** The app walks a person from "I got a job offer / a scholarship / I want to try" to the first week abroad: which documents they need and where to get each one, how the visa process works, what it should really cost, whether their agent and papers are genuine, and what to do if something goes wrong. It explains and checks. It never applies for a visa, passport or ticket on anyone's behalf, and never asks for a government portal password.

**Two hero stories. The demo and the video follow these.**

1. *Ahmed, 27, Pakistan to Saudi Arabia, work.* An agent offers a driver job and asks for a large fee in cash. Ahmed photographs the offer letter and records a voice note in Urdu about what the agent promised. Pardes Guard reads both and finds that the contract salary is lower than promised, the fee is above the legal maximum, and the licence belongs to a different company: red stamp. It shows him the official route, the real costs, how to find a licensed promoter, and his personal journey to departure. Later in Riyadh his wage comes short. He opens a case, the app drafts a letter that he approves and sends himself, and his family follows progress with a share code.
2. *Ayesha, 22, Pakistan to the United Kingdom, study.* She has an admission and scholarship letter. The app checks the letter for scam signs, builds her journey (CAS, English test, funds, TB test, visa application), scans her documents for problems (passport expiry, name mismatch), explains the visa form in Urdu, and lets her practise a credibility interview by voice with Gemini Live.

The team will verify the content for these two routes (PK to SA work, PK to GB student) from official sources. All other countries stay `draft`.

## 3. What is in the zip, and what to keep

Rebuild the frontend UI from scratch: pages, components, styles and navigation. Keep and reuse the tested logic; do not rewrite it.

Keep:
- `frontend/lib/engine/`: backend logic ported to TypeScript, 28 passing tests (`npm test`). Modules: `text` (normalising, fuzzy match, masking, injection screen, SHA-256), `packs`, `recruiters` (including the borrowed-licence check and CSV parser), `rules` (evaluate, score, nextSteps, topReasons), `forensics` (canvas dHash layout fingerprint), `eligibility`, `wage`, `cases` (escalation ladder, approval gate, `advance()`), `evidence` (SHA-256 chain), `network` (hashed signals, rings, alerts). You may refactor; keep the tests passing and add tests for new logic.
- `frontend/lib/types.ts`: the data shapes. Extend them, don't break them.
- `frontend/data/packs.json` (10 country packs, all draft) and `recruiters.json` (10 fictional sample rows), generated by `npm run data` from `frontend/scripts/export_data.py` with the backend validators.
- `frontend/lib/i18n.tsx`: English and Urdu dictionaries, 414 keys each. Carry the strings into the new structure and rewrite wording where the new UI needs it.
- `frontend/lib/images.ts` (shrinks large images before upload) and `lib/storage.ts`.
- `backend/`: the paid production version (FastAPI, Google ADK agents, Cloud Run, Cloud KMS, Sensitive Data Protection, Model Armor, Spanner Graph), 67 passing tests. Do not deploy it. It stays in the repo as the production design. Reuse its prompts from `backend/app/llm/prompts.py`: `READ_DOCUMENT`, `READ_STATEMENT`, `EXPLAIN_VERDICT`, `DRAFT_LETTER`, `RESEARCH_REQUIREMENTS`, `STRUCTURE_REQUIREMENTS`, `GUARDIAN_INSTRUCTION`, `LANGUAGE_NAMES`.
- `infra/`: Cloud Run scripts, keep as they are. Change `firebase.json` as described in section 4.

Replace:
- Everything in `frontend/app/` and `frontend/components/`.
- `frontend/lib/api.ts`, which today calls the backend over HTTP. Replace it with a client that runs on the engine, Firestore and Firebase AI Logic. Its shape may change, since the pages are new.

## 4. Architecture ($0)

A static Next.js 16.4 export (`output: 'export'`, React 19.3, TypeScript 5.9) served by Firebase Hosting. The browser talks only to Firebase Authentication, Cloud Firestore and Firebase AI Logic with the Gemini Developer API backend. No Cloud Run, no Cloud Functions, no Cloud Storage (Cloud Storage for Firebase now needs the Blaze plan). Do not deploy anything outside Firebase unless the team tells you to.

- `lib/store.ts`: a `DataStore` interface with `FirestoreStore` (used when `NEXT_PUBLIC_FIREBASE_*` config exists) and `LocalStore` (localStorage, for guest mode, the offline demo and tests).
- `lib/ai.ts`: an `AIProvider` interface with `GeminiProvider` (Firebase AI Logic) and `OfflineProvider` (returns nothing, so the app falls back to rules-only results and template letters). The app must stay usable when AI is unavailable or out of quota.
- Gemini never decides a verdict, a fee, an eligibility result or a deadline. It reads, extracts, explains and drafts. Code decides.
- Case escalation timers: call `advance()` on the user's cases when the app opens. There is no scheduler on the free plan.
- Evidence files: the bytes stay in IndexedDB on the device; `EvidenceRecord`s go to Firestore with a server timestamp; export is a ZIP built with JSZip (files plus `manifest.json`).

**Firebase AI Logic API, checked against the installed `firebase` 13.0.0 type definitions.**
- `getAI(app, { backend: new GoogleAIBackend() })`, then `getGenerativeModel(ai, ModelParams | HybridParams)`.
- JSON output: `generationConfig: { responseMimeType: 'application/json', responseSchema }`, or `responseJsonSchema` for a plain JSON Schema.
- `result.response.text()` and `result.response.functionCalls()`. Chat: `model.startChat()`, then `chat.sendMessage()`. Answer a call with `FunctionResponse { id?, name, response }`. Message parts carry a `type` field: `'text' | 'inlineData' | 'functionResponse'`.
- Tools: `{ functionDeclarations }`, `{ googleSearch: {} }`, `{ googleMaps: {} }`, `{ urlContext: {} }`, code execution.
- Hybrid: `{ mode: InferenceMode.PREFER_ON_DEVICE, inCloudParams: { model } }`.
- Live (Preview in Firebase): `getLiveGenerativeModel(ai, { model: 'gemini-3.1-flash-live-preview', generationConfig, tools, systemInstruction })`, then `await model.connect()`, then `startAudioConversation(session, { functionCallingHandler })`, which returns a controller with `stop()`. `LiveGenerationConfig` has `inputAudioTranscription` and `outputAudioTranscription`; check how to read transcripts while `startAudioConversation` is running.

**Models and free-tier facts (Google's Gemini API pricing page, October 2026).**
- Model chain: `gemini-3.8-flash`, then `gemini-3.5-flash-lite` on quota errors, then `gemma-4-31b-it` (check that AI Logic accepts it; for Gemma, ask for JSON in the prompt and parse it from text), then rules only.
- Do not use `gemini-3.1-pro-preview`. It has no free tier.
- Grounding with Google Search and Google Maps is not available on the free tier for `gemini-3.8-flash` and `gemini-3.5-flash-lite`. Search grounding is supported on the free tier for the Live model. So put `googleSearch` and `googleMaps` on text models behind `NEXT_PUBLIC_GROUNDING=on` (off by default), and in $0 mode show plain Google Search and Google Maps links instead.
- Wherever grounding is on, follow Google's display rules: render `groundingMetadata.searchEntryPoint.renderedContent` for Search, list sources right after the answer, and for Maps show each source title linked to its URI with the attribution text "Google Maps" unmodified and `translate="no"`.
- URL context: the fetched page counts as input tokens, so it should work on the free tier. Test it.
- Google may use free-tier content to improve its products. The demo uses fictional data only, and upload screens show a one-line notice.

**Firestore collections and rules.** Write a new `firestore.rules`; the current `infra/firestore.rules` denies everything because the paid build only uses its own server. Staff means a `roles/{uid}` document with `role` in `['ngo', 'admin']`, written only from the Firebase console.

| Collection | Read | Write |
|---|---|---|
| `checks`, `cases`, `evidence`, `journeys` (`journeys/{uid}`) | owner (`owner_id == uid`) or staff | owner only |
| `ratings/{license}_{uid}` | signed-in users | that uid only |
| `signals/{id}` | staff only | create by a signed-in user with `owner_id == uid`; delete by that owner |
| `reports/{id}` | staff only | create by a signed-in user |
| `shares/{code}` | `get` by anyone, no `list` | the case owner |
| `riskIndex/{key}`, `packOverrides/{country}`, `config/*` | anyone | staff only |
| `contentDrafts/{id}` | staff | staff |
| `roles/{uid}` | that uid | nobody from the client |

A Firestore document is capped at 1 MiB, so split large lists (the recruiter list) across documents. Add rules tests with the Firestore emulator if you can run it; if you cannot, say so.

`firebase.json`: remove the `/api/**` Cloud Run rewrite, point `firestore.rules` at the new file, and keep the security headers. If SOS shares location, change `Permissions-Policy` from `geolocation=()` to `geolocation=(self)` and ask for consent in the UI.

## 5. Scope

The team's list has 40 feature names. They collapse into the modules below (the numbers refer to that list). Build P1 first and make each module work end to end before starting the next. Start P2 only when all of P1 works. P3 only if everything else is done.

### P1: must work by 17 October

1. **Start and My Journey dashboard (features 2, 10, 38, 40).** Onboarding asks three questions with big picture tiles: why (job offer / scholarship or admission / want to try), from (country), to (country and route). The app builds a personal roadmap from the route's steps, documents, departure checklist and arrival checklist. Each item shows who does it (you, employer, university, government), its status and its official link. Home always shows "your next step". The progress view shows the stages as passport pages that get stamped when done, with a simple progress score that lists its reasons (items done, red flags still open).
   *Acceptance:* both hero routes produce a complete journey; status changes survive a reload in both FirestoreStore and LocalStore; works in English and Urdu.
2. **Documents guide (part of 2).** One page per document: who issues it, online or office, what to bring, steps, typical time, official link, source and last-verified date, and a draft or verified badge. Pakistan examples the team will verify: passport (Directorate General of Immigration and Passports), CNIC and FRC (NADRA), police character certificate, degree attestation (HEC), MOFA attestation, IBCC equivalence, Gulf medical (Wafid/GAMCA), Protector registration (Bureau of Emigration and Overseas Employment).
   Extend the pack schema in both `backend/app/schemas.py` (validators) and `lib/types.ts`, then run `npm run data`. Origin packs get `documents[]` (id, title, issued_by, online_or_office, steps[], bring[], typical_time, official_url, sources[], status, last_verified). Routes reference document ids and get `fees[]` (item, amount, currency, source, last_verified) and `interview_topics[]`. Destination packs get `arrival_checklist[]`. Leave unknown values empty and `draft`.
3. **Check: Fraud Risk Radar (features 1, 21, 25, 28, 29, 39).** The user uploads photos or PDFs of an offer letter, contract, visa or admission letter, and can record a voice note. Gemini extracts fields (`READ_DOCUMENT`, `READ_STATEMENT`; schemas `ExtractedDocument` and `WorkerStatement`). Code then runs `screenForInjection`, `layoutHash`, the recruiter check (licence, borrowed licence, NGO warnings from `riskIndex`), and `evaluate` and `score`.
   The result shows: the verdict stamp (red, amber or green, each with its own icon and word); top reasons; every flag with its evidence and official source; next steps; an explanation in the user's language with a Listen button; and an AI translation of the document labelled "AI translation, not certified".
   *Acceptance:* a fictional fraudulent sample gives red with the right flags; a clean sample gives green; a prompt-injection sample is caught; with AI off, a manual entry form still produces a rules-based result.
4. **True Cost and Agent Fee Analyzer (features 5, 17).** Lists each official cost of the route with source and date. The user enters what the agent is asking. The app shows the difference and flags anything above `max_recruitment_fee`. Where a fee has no source, no number is shown, only "check the official site".
5. **Document Readiness Scanner (features 6, 15, 31).** The user photographs their documents. Gemini extracts name, dates and passport expiry. Code checks the months left on the passport against the route's rule, and the name spelling across documents. Images are not stored, only results. Passport expiry becomes a deadline in the journey.
6. **Interview practice and voice assistant (features 4, 13).** A Live voice session in the user's language. Interview mode builds its system instruction from the route's `interview_topics` and ends with a short scorecard from `gemini-3.8-flash`, clearly labelled as practice. Assistant mode answers questions through function calls into the app (recruiter check, route rules, eligibility, wage check). Show a clear mic state and a stop button, and fall back to text chat when Live is unavailable.
7. **Already-built flows, rebuilt in the new UI and wired to the $0 stack:** eligibility (30), departure checklist (18), recruiter search and rating (21), wage check (23), cases with the escalation ladder, approval gate and Gemini-drafted letters (23), evidence vault (24), family view by share code (7), and emergency SOS (3) with helplines (27). SOS adds a quick-exit button that switches to a neutral screen, and WhatsApp share links (`https://wa.me/?text=...`) that the user sends themselves.
8. **Privacy controls (37).** "Delete all my data" deletes the user's Firestore documents (including their signals, whose ids you keep in the user's own data), clears IndexedDB, then deletes the Auth user (Firebase may require a fresh sign-in). Also: a plain page on what is stored, and an opt-in switch for sharing fraud signals.
9. **Languages:** see section 6.

### P2
- NGO dashboard: rings, alerts, review queue, publishing warnings to `riskIndex`, confirming fake layouts (9, 33).
- Community scam reports into `reports`, never public before staff review (11).
- Deadlines manager with Google Calendar template links, `https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=...` (20, 31, 35).
- Visa form guide (16).
- Scholarship and admission letter checks with official register links (14).
- Post-arrival guide (19).
- Employer check with Google Maps and Search links (22).
- Simple mode (12).
- Offline kit: a hand-written service worker caching the app shell, packs, helplines and checklists (8, 36).

### P3
- Admin content research with URL context: the admin gives an official URL, Gemini drafts, the admin approves.
- Recruiter CSV import.
- Anonymous CSV export for the BigQuery sandbox, plus a Looker Studio dashboard (34).
- Hybrid on-device mode.

## 6. Languages

The target users speak Urdu, Punjabi (Shahmukhi), Pashto, Hindi, Bengali, Nepali, Filipino, Sinhala, Tamil and Indonesian. Arabic matters too, for Gulf contracts.

- UI: English and Urdu complete. Add Hindi, Bengali, Nepali and Filipino, drafted with Gemini and flagged `machine: true` so the UI shows "machine translation". Missing keys fall back to English. Other languages use the English UI.
- AI output (explanations, letters, assistant, interview): all the languages above. Extend `LANGUAGE_NAMES` (add `si` and `ta`; the file uses `tl` for Tagalog, so pick one code for Filipino and use it everywhere). For Live, set the language in the system instruction. Google's Live API guide lists all of these languages as supported.
- Right-to-left: `ur`, `pa` (Shahmukhi), `ps`, `ar`, `sd`. Use CSS logical properties everywhere so layouts mirror without special cases. Icons that show direction (back, next, progress) flip in RTL; others don't.
- Fonts from Google Fonts, loaded only for the active locale: Atkinson Hyperlegible Next (Latin), Noto Nastaliq Urdu (Urdu, Punjabi), Noto Naskh Arabic (Pashto, Arabic, Sindhi), Noto Sans Devanagari (Hindi, Nepali), Noto Sans Bengali, Noto Sans Sinhala, Noto Sans Tamil. Nastaliq needs a line height of about 2 and a slightly larger size; check it in screenshots.
- Never translate numbers, fees, phone numbers or URLs. Always show amounts with their currency.
- Phone voices for "Listen" vary by device. If there is no voice for the language, use Gemini Live audio or hide the button.

## 7. Design direction (this is where we win UX)

The old UI was correct but plain. Make it feel made for a first-time traveller holding a cheap phone, not like a SaaS dashboard. Below is the direction; you own the details.

**Concept: "a passport that protects you."** The visual language comes from travel documents: passport pages, entry stamps, boarding passes, and the fine security-print line patterns on passports and banknotes. Use these as inspiration only. No national emblems, seals or flags used as authority, and nothing that could be mistaken for a real government document or a government website.

**One signature moment: the verdict stamp.** When a check finishes, an ink stamp lands on the document card: a short press (about 300 ms, a slight scale and rotation, ink texture from an SVG filter), and then it stays. Red "STOP", amber "CHECK", green "LOOKS OK", all translated, each with its own icon shape so colour is never the only signal. The same stamp language marks completed journey stages on the passport pages. Everything else stays calm: no other entrance animations. With `prefers-reduced-motion`, the stamp appears without movement.

**Tokens.** Keep these; they are already distinctive. Refine if needed.
- Paper `#eef2ee`, sheet `#ffffff`, ink `#15211b`, soft ink `#4a5a52`, rule `#c9d4cc`.
- Passport green `#0e4a37` (primary), green tint `#dfeae3`.
- Stamp red `#b3242a`, amber `#9a6a12`, OK green `#1d6e47`, each with a tint.
- Focus `#1f6feb`. A full dark theme (the current values are in `app/globals.css`).
- Security-print pattern: very fine, low-contrast lines, used only on the home header and the journey pages, never behind body text.
- Radius 10px on cards and 6px on chips. The stamp and the passport pages may break the grid.

**Type.** Atkinson Hyperlegible Next for Latin script; it was designed for low vision, which suits these users. Base size 18px on mobile with line height 1.5 (Nastaliq about 2). A clear scale such as 15, 18, 22, 28, 36. Sentence case everywhere, and no all-caps labels except inside the stamp. Monospace only for codes people must read out or type (share code, case reference).

**Layout and navigation.**
- Mobile first: design at 360 × 800, then scale up. Single column with a maximum width of 680px. NGO and admin screens may widen to 980px with tables.
- A bottom bar with four items: Journey, Check, Help, More. An SOS button reachable from every screen, not hidden in a menu.
- One primary action per screen, at thumb height. Tap targets at least 52px.
- Every choice is an icon plus a label, never an icon alone. Use one icon set from npm (Lucide or Phosphor), never emoji.
- Home: a "your next step" card in boarding-pass style (from, to, what to do now, one button), the journey progress, quick actions and SOS.

**Low-literacy UX.**
- Voice in and voice out: a mic on every text input, and a Listen button on every result and every document page.
- Plain words at about a 10-year-old's reading level, in short sentences. Explain every term the first time it appears (CAS, Protector, attestation).
- Simple mode: at most three choices per screen, advanced screens hidden, larger text.
- Progress is always visible and there are no dead ends. Every error says what happened and what to do next, in the user's language.
- Confirm before anything that cannot be undone (deleting data, marking a letter as sent).

**Trust UX.**
- Every rule, fee and helpline shows its source as a tappable chip with the last-verified date. Draft content carries a visible "draft" badge.
- On results, one short line: "AI read your document. The decision comes from fixed rules." Plus a plain-language legal disclaimer.
- Sample and fictional data is visibly marked as sample.

**Quality floor.** WCAG 2.2 AA: text contrast of at least 4.5:1, visible focus, labels for screen readers, usable at 200% text size, fully keyboard-usable. Fast on a low-end Android over 3G: small JavaScript per route, fonts per locale, images shrunk before upload, and skeletons rather than spinners for content.

**Avoid; these make a UI look generated:** gradient hero sections; a grid of identical rounded cards with the same soft shadow; tracked-out all-caps eyebrow labels; emoji icons; "→" glued to every button; glassmorphism; stock illustrations of smiling people; decorative 01/02/03 numbers on things that are not steps; fade-in animations scattered across the page.

**Process.**
1. Before building screens, write `frontend/DESIGN.md`: tokens, type scale, components, the stamp, and ASCII wireframes of 3 or 4 key screens.
2. Build a `/styleguide` route that shows every component in light and dark, English and Urdu.
3. Build the screens from those components only.
4. Screenshot every P1 screen at 360px and 1280px, in English and Urdu, light and dark. Look at the screenshots and fix what is off before you report.

## 8. Screens (P1)

- Welcome and language picker, with big buttons that write each language in its own script.
- Sign in with Google. Guest mode is allowed, using LocalStore, with a note that the data stays on this phone.
- Onboarding (the three tile questions), which creates the journey.
- Home: next step, progress, quick actions, SOS.
- Journey: stages as passport pages. Each item opens a detail view with status, who does it, link and source.
- Document page (from the documents guide), plus the readiness scan.
- Cost analyzer.
- Check flow:
  - Upload or record.
  - Progress screen that says what is happening in plain words.
  - Result: stamp, reasons, flags with evidence and sources, next steps, explanation, Listen, translation, "open a case", "report this agent".
- Recruiter search and recruiter profile.
- Eligibility.
- Interview practice and assistant (voice, with a text fallback).
- Departure checklist. Arrival guide (P2).
- Cases: list, case detail (ladder, letter editor, approve or decline, mark as sent), and the wage check.
- Vault: list, add, verify the chain, export the ZIP.
- Family: enter a code, then see the progress view.
- SOS: helplines, quick exit, share via WhatsApp, open an emergency case.
- Settings: language, simple mode, theme, privacy (what we store, delete everything), sign out.
- NGO and admin screens (P2 and P3).

## 9. Security and privacy

- Firestore rules as in section 4. Never trust a role that comes from the client.
- Mask phone and account numbers (show only the last 4 digits) in the UI and in letters.
- Treat everything Gemini returns as data, never as instructions. Run the injection screen on extracted text.
- Never ask for a government portal password, and never submit a form on the user's behalf.
- Show the free-tier notice on upload screens. Use fictional data only in the demo.
- Phones and account numbers are hashed before they leave the device as fraud signals (existing `network.ts`). This is pseudonymous, not secret; say so on the privacy page.
- Keep the existing security headers.

## 10. Quality bar and tests

- `npm run typecheck`, `npm test` and `npm run build` all pass. If you change `schemas.py`, the backend tests (`cd backend && pytest`) must still pass.
- Unit tests for every new engine function: journey builder, cost analyzer, readiness rules, language fallback.
- Playwright smoke tests for both hero stories using LocalStore and OfflineProvider (no network), with screenshots.
- An axe-core accessibility check on the P1 screens, with no serious violations.
- A seed script with fictional personas and fictional sample documents, clearly marked SAMPLE and using made-up company names, so a judge can try the app without uploading anything. Add a "Try a sample" button on Check.
- `README.md`: what the app is, the live link, how to run it, an architecture diagram, the honest $0-versus-production note, the Google tools used, and the test commands.

## 11. Wording that must stay true (README and deck)

> The live demo runs entirely on Firebase's no-cost plan, with Gemini through Firebase AI Logic. The production design, with ADK agents on Cloud Run, Cloud KMS-signed evidence, Sensitive Data Protection, Model Armor and a Spanner Graph fraud network, is implemented in the repository with unit tests and deployment scripts.

Do not claim that the production backend ran against live Google services.

## 12. Order of work

- **Phase 1 (13 to 14 October).**
  - Design system, `DESIGN.md` and the styleguide.
  - i18n structure with English, Urdu and RTL.
  - Store and AI providers, and the Firebase wiring.
  - The pack schema extension.
  - Journey and the documents guide.
  - Report with screenshots.
- **Phase 2 (15 October).** Check / Fraud Risk Radar, cost analyzer, readiness scan, sample data. Report.
- **Phase 3 (16 October).**
  - Live interview practice and the assistant.
  - Cases, vault, family, SOS, wage check and eligibility in the new UI.
  - Privacy controls.
  - The extra languages.
  - Report.
- **Phase 4 (17 October).**
  - The P2 items that fit.
  - Polish and accessibility.
  - Playwright tests and the README.
  - Deploy to Firebase Hosting.
  - Final report listing what was and was not tested.
- **18 October.** Fixes only.

If you fall behind, cut P2 before you cut quality on P1.

## 13. Setup the team does (tell them when you need it)

1. Unlink billing so the project stays on Spark: `gcloud billing projects unlink pardes-guard`.
2. In the Firebase console:
   - Add the existing Google Cloud project `pardes-guard`.
   - Enable Authentication with the Google provider.
   - Create the Firestore database.
   - Open AI Logic and choose the Gemini Developer API.
   - Register a web app and copy its config into `frontend/.env.local`.
3. Add their own uid to `roles/{uid}` with `role: 'admin'`.
4. Optional: App Check (confirm it stays free before enabling).
5. Deploy: `firebase deploy --only hosting,firestore:rules`.

## 14. Never

- Invent official URLs, offices, fees, phone numbers or rules.
- Let Gemini decide a verdict, a fee or eligibility.
- Store passport images, or use real people's documents in the demo.
- Send anything to anyone without the user tapping to approve it.
- Claim something was tested when it was not.
