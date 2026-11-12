# Trazo

A mobile-first web app. The patient photographs a doctor's prescription on their
phone, in a mobile browser, and gets back each medicine with its strength,
take-times in plain words, duration, and a status word.

> **This is a reading aid, not medical advice. Confirm with your pharmacist.**

**Core rule:** Trazo never guesses. Anything it cannot read clearly is flagged
**Check this** or **Unclear**, with a plain-words reason — never filled in.

This is a student project. It is not clinically validated.

## Measured results

From the one-command evaluation harness on real, verified prescription photos
(full method and history: [eval/RESULTS.md](eval/RESULTS.md), rules:
[eval/scoring_rules.md](eval/scoring_rules.md)):

| Metric | Value |
|---|---|
| **Wrong and NOT flagged (dangerous)** | **0 of 38 items** |
| **Missed medicines** | **0 of 38 items** |
| Name accuracy | 0.774 |
| Timing accuracy | 0.516 |
| Wrong but flagged | 26 of 38 items |

The headline is the safety pair: the app never shows a confident wrong answer
and never drops a medicine. What it can't confirm, it flags.

## How it works

```
photo (mobile browser)
   -> resized in the browser, JPEG
   -> EXIF rotation fix + resize on the server            app/image_utils.py
   -> photo quality check: too blurry / dark / small?     app/clean.py
        -> if it fails: "take it again", no model call
   -> vision model reads it into JSON                     app/extract.py
   -> the JSON reply is parsed, never guessed at          app/parse_utils.py
   -> each name is matched against the medicine list      app/match.py
   -> timing codes are decoded                            app/timing.py
   -> a status word is decided for every row              app/status.py
   -> saved corrections are offered, always flagged       app/corrections.py
   -> rows + the safety banner, photo discarded           app/pipeline.py
```

A row is **OK** only if the model did not flag it unreadable, the name matched
the list at or above the accept threshold, the timing code is known, and no
second medicine scores nearly as close. Otherwise the row is **Check this**
(did-you-mean suggestions and verified unknown-name wording included) or
**Unclear** — always with a plain-words reason.

## Deploy (Vercel)

The repo is Vercel-ready: `api/index.py` is the serverless entry,
`vercel.json` routes everything to it, and the read-only medicine database
ships in the bundle.

1. Import `VineshF1/trazo` in the Vercel dashboard (framework preset: Other).
2. Add the environment variable `NVIDIA_API_KEY`.
3. Deploy.

Notes: the corrections database (the only thing the app writes) goes to
`/tmp` on the read-only serverless filesystem; the model timeout is clamped
to 55 s under the Hobby plan's 60 s function limit, so unusually slow model
responses return a readable timeout instead of hanging the request.

## Run locally

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows; .venv/bin/activate elsewhere
pip install -r requirements.txt
cp .env.example .env                 # paste your NVIDIA_API_KEY
python scripts/load_medicines.py data/medicines_list.csv
uvicorn main:app --reload            # http://127.0.0.1:8000
```

The medicine list CSV needs the columns `brand_name, generic_name, strength,
use`. A name that was searched online and matches no medicine goes in
`data/unknown_names.csv`, so the app can flag it with wording that says so
instead of a generic Check this.

## Evaluation

```bash
python eval/run_eval.py --mode pipeline            # the full pipeline
python eval/run_eval.py --mode pipeline --final    # adds locked group B, once
```

Images come from `tests_local/prescriptions/` (never committed), the answer
key from `eval/expected.csv` (never committed). Results land in
`eval/results/` and `eval/RESULTS.md`.

## Privacy

- Photos are processed in memory and never written to disk.
- No analytics, no telemetry, no external CDNs, no accounts.
- The only stored text is a correction's pair (the reading and what the user
  typed). Never a photo, never a user id.

## Limits

- Small test set: say "tested on N prescriptions", not "proven".
- List coverage: a missing medicine is a list limit, not a model failure.
- Free-tier model API: can be rate-limited, slow or unavailable.
- No dose advice, no interaction checks, no diagnosis. By design.

## Repository layout

| Path | Purpose |
|---|---|
| `main.py` | FastAPI entry point: `/health`, `/read`, `/correct`, the static page. |
| `api/index.py` | Vercel serverless entry point. |
| `vercel.json` | Routing and function limits for the Vercel deployment. |
| `app/config.py` | Model ID, thresholds, image and quality settings. |
| `app/extract.py` | The model call and its error handling. |
| `app/match.py` | Fuzzy matching against brand and generic names. |
| `app/unknowns.py` | Names verified online as "no medicine by this name". |
| `app/status.py` | The OK / Check this / Unclear rule. |
| `app/pipeline.py` | The one place the steps are combined. |
| `eval/` | The harness, scoring rules, and results. |
| `scripts/` | `load_medicines.py`, `try_one.py`, `rescore_raw.py`. |
| `static/` | The page: `index.html`, `style.css`, `app.js`, one self-hosted font. |
| `prompts/` | The extraction prompt and the baseline prompt. |
