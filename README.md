# Trazo

A mobile-first web app. The patient photographs a doctor's prescription on their
phone, in a mobile browser, and gets back the medicine names, strengths, timing and
duration written on the page.

> **This is a reading aid, not medical advice. Confirm with your pharmacist.**

**Core rule:** Trazo never guesses. Anything it cannot read clearly is flagged as
unreadable instead of being filled in.

This is a student project. It is not clinically validated. The results table below
stays `TBD` until it is filled in from a real run of the evaluation harness on real,
verified prescriptions.

## How it works

```
photo (mobile browser)
   -> resized in the browser, JPEG
   -> rotation fixed from EXIF, resized on the server       app/image_utils.py
   -> photo quality check: too blurry / dark / small?       app/clean.py
        -> if it fails: "take it again", no model call
   -> GLM 5.3 Flash reads it into JSON                      app/extract.py
   -> the JSON reply is parsed, never guessed at             app/parse_utils.py
   -> each name is matched against the medicine list         app/match.py
   -> timing codes are decoded                               app/timing.py
   -> a status word is decided for every row                 app/status.py
   -> saved corrections are offered, always flagged          app/corrections.py
   -> rows + the safety banner, photo discarded              app/pipeline.py
```

Every row carries one of three status words. A row is **OK** only if the model did
not flag it unreadable, the medicine name matched the list at or above the accept
threshold, the timing code is known, and no second medicine name scores nearly as
close. Anything else is **Check this** or **Unclear**, always with a plain-words
reason.

## Requirements

- Python 3.10 or newer. Developed and verified on CPython 3.12.
- An NVIDIA API key for `z-ai/glm-5.3-flash` on NVIDIA Build.

## Run it in 5 steps

1. Install:

   ```bash
   python -m venv .venv
   source .venv/Scripts/activate   # Windows (git-bash); use .venv/bin/activate elsewhere
   pip install -r requirements.txt
   ```

2. Load a medicine list. The CSV must have the columns
   `brand_name, generic_name, strength, use`:

   ```bash
   python scripts/load_medicines.py path/to/medicines.csv
   ```

3. Put your key in `.env` and start the server. The key is used
   server side only and never reaches the page:

   ```bash
   cp .env.example .env        # then paste your key after NVIDIA_API_KEY=
   uvicorn main:app --reload
   ```

4. Check it is up, and read one prescription from the command line:

   ```bash
   curl http://127.0.0.1:8000/health
   python scripts/try_one.py path/to/prescription.jpg
   ```

5. Open the page on your phone, on the same Wi-Fi as this machine:

   ```
   http://<your-laptop-ip>:8000/
   ```

## One-command evaluation

Anyone can reproduce the numbers. The harness reads images from
`tests_local/prescriptions/` and answers from `eval/expected.csv`:

```bash
python eval/run_eval.py --mode baseline     # plain prompt, same model: can never flag
python eval/run_eval.py --mode pipeline     # the full pipeline
python eval/run_eval.py --mode pipeline --final   # adds group B, once, for the report
```

It writes a per-item CSV and a markdown table under `eval/results/`, plus the raw
model replies. Group B only runs with `--final`, and the harness warns that it is
meant to be used once.

The scoring rules are not decided by the code. Open questions are listed in
`eval/scoring_rules.md` and are answered by the human before group B is run.

## Results

**TBD: filled from `eval/run_eval.py` output.**

| Metric | Baseline | Pipeline |
|---|---|---|
| Name accuracy | TBD | TBD |
| Timing accuracy | TBD | TBD |
| Unclear rate | TBD | TBD |
| Wrong but flagged | TBD | TBD |
| Wrong and NOT flagged (dangerous) | TBD | TBD |
| Seconds per image | TBD | TBD |

Printed and handwritten prescriptions are reported separately by the harness. No
number belongs in this table that was not produced by a real run.

## Privacy

- Uploaded photos are processed in memory and never written to disk.
- No analytics, no telemetry, no third-party scripts, no external CDNs.
- No accounts. The only thing ever stored is a correction's text: the reading and
  what the user typed. Never a photo, never a user id.
- Only the route, method and status code are logged. A validation failure logs the
  exception type, not its message, because that message can quote a reading.

## Limits

- **Small test set.** The plan targets 20 to 30 prescriptions, which is a rough
  sample. Say "tested on N prescriptions", not "proven".
- **Medicine list coverage.** Matching can only find medicines that are in the list
  loaded into `data/medicines.db`. A missing medicine is a list limit, not a model
  failure. Report the coverage.
- **One model.** GLM 5.3 Flash via a free-tier API. It can be rate-limited, slow or
  unavailable, and it is not clinically validated. A different model would move
  every number in the table.
- **Photo quality thresholds are starting guesses** (`app/config.py`) and need
  tuning on real photos. A ceiling that is too low rejects good photos; a floor that
  is too high lets unreadable ones through.
- **Reads one page per photo.** A prescription with two pages, or several rows
  crowded together, is where this fails.
- **No dose advice, no interaction checks, no diagnosis.** By design.

## Repository layout

| Path | Purpose |
|---|---|
| `main.py` | FastAPI entry point: `/health`, `/read`, `/correct`, the static page. |
| `app/config.py` | Model ID, thresholds, image and quality settings. All starting guesses. |
| `app/schema.py` | The extraction schema and its normalization. |
| `app/parse_utils.py` | Robust JSON parsing of the model's reply. |
| `app/extract.py` | The model call, its errors, and the retry-once rule. |
| `app/image_utils.py` | EXIF rotation, resize, JPEG encode. |
| `app/clean.py` | Photo quality check (blur, brightness, size). |
| `app/medicines.py` | Medicine list storage in SQLite. |
| `app/match.py` | Fuzzy matching against brand and generic names. |
| `app/timing.py` | The timing-code decoder. |
| `app/status.py` | The OK / Check this / Unclear rule. |
| `app/corrections.py` | The verified-correction table. |
| `app/pipeline.py` | The one place the steps are combined. |
| `eval/scoring.py` | Pairing and scoring rules. |
| `eval/run_eval.py` | The one-command harness. |
| `scripts/` | `try_one.py` (one image, one real call), `load_medicines.py`. |
| `tests/` | pytest suite: synthetic strings and generated images only. |
| `tests_local/prescriptions/` | Real prescriptions. Never committed. |
| `data/` | SQLite databases. Not committed. |
| `static/` | The page: `index.html`, `style.css`, `app.js`, plus one self-hosted display font under `fonts/`. |
| `prompts/` | The extraction prompt and the baseline prompt. |
