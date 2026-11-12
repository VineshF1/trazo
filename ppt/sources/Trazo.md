# Trazo: Build Prompt for an AI Coding Agent

## How to use this file

- If `prescription-reader-project.md` is in the repo, the agent should read it first. It is the full plan. This file is the build instructions derived from it.
- **Work one phase at a time.** Tell the agent: "Do Phase N only." Do not ask for the whole app in one go.
- Phase 1 and Phase 3 end with a **STOP** line. The agent must stop there and wait for the human, because the next step needs a real prescription or a human decision.

---

## 1. Your role

You are building **Trazo**, a mobile-first web app for a college mini project and a public GitHub repo. You write simple, readable Python and plain HTML, CSS and JavaScript. You follow this file exactly. When this file is silent, choose the simplest option and say what you chose. Ask a question only if you are blocked.

---

## 2. What Trazo is

- A patient takes a photo of a doctor's prescription on their phone, in a mobile browser.
- A vision model reads it. The result is a list of medicines: name, strength, when to take, for how many days.
- **Core rule: it never guesses.** Anything it cannot read clearly is flagged and shown as unreadable, not filled in.
- Every result carries this banner: "This is a reading aid, not medical advice. Confirm with your pharmacist."
- It is a student project with measured accuracy. It is not clinically validated.
- The name means "pen stroke" in Spanish.

---

## 3. Non-negotiable rules

### Honesty
- **Never invent results.** Do not make up accuracy numbers, test outputs, sample prescriptions that look real, or "expected" figures. Leave results tables as `TBD` until the human's real test run fills them in.
- **Never claim** the app is "safe", "accurate" or "ready for patients". Do not write marketing copy.
- If something is unverified, write `TODO: verify` in the code or README and tell the human in your report.

### Safety
- Never let the model's guess replace an unreadable word. If a word is unreadable, `name` is null and `unclear` is true.
- No dose advice, no dose changes, no diagnosis, no interaction warnings.
- A row is **OK** only if every check passes (section 8). Otherwise it is **Check this** or **Unclear**.
- Learned corrections only suggest, and always stay flagged "Check this".

### Privacy
- **Never store uploaded photos.** Process in memory and discard.
- Never log medicine names together with any user identity. No analytics, telemetry, or third-party scripts. No external CDNs.

### Scope
Build only what is listed in section 5. Do **not** add: a second model, model comparison, reminders, look-alike pair lists, interaction checks, user accounts, dark mode, a native app, offline mode, installable-app features, Telugu or Hindi text, or any framework.

---

## 4. Stack and constraints

| Part | Use |
|---|---|
| Language | Python 3.10 or newer (starting guess) |
| Backend | FastAPI, served by uvicorn |
| Frontend | One static page: `index.html`, `style.css`, `app.js`. No React, no build step, no CSS framework, no libraries from a CDN |
| Model | GLM 5.3 Flash on NVIDIA Build, via the `openai` Python package |
| Model ID | `z-ai/glm-5.3-flash` (copy from the NVIDIA model page before use, and keep it in `config.py`) |
| API base URL | `https://integrate.api.nvidia.com/v1` |
| API key | env var `NVIDIA_API_KEY`, server side only. Never in the page or JavaScript |
| Images | Pillow (`ImageOps.exif_transpose` for rotation) and OpenCV for cleanup and quality check |
| Matching | RapidFuzz |
| Storage | SQLite (`data/medicines.db`, `data/corrections.db`) |
| Tests | pytest |
| Eval | pandas |

---

## 5. Scope

### Core
1. Mobile-first page: camera capture, gallery pick, photo preview
2. Photo resized in the browser, rotation fixed on the server
3. Extraction to JSON with GLM 5.3 Flash
4. Medicine database matching
5. Timing code decoder
6. Status flags: OK, Check this, Unclear
7. Safety banner
8. Evaluation harness with baseline vs pipeline comparison

### Add-ons (only when asked, in this order)
1. Photo quality check
2. Correction step and correction table

---

## 6. Phases

After each phase, send a short report: what you built, how to run it, what is untested, and any assumption you made. Then stop and wait.

### Phase 0: Project setup
- Create the modules and folders that the later phases name.
- `config.py` with the model ID, base URL, matching thresholds (accept 90, review 70), and image resize target (longest side 1600 px, JPEG quality 0.8). Mark all of these `starting guess`.
- `requirements.txt` and a minimal `README.md` with the disclaimer. No results numbers.
- **Done when:** `pip install -r requirements.txt` works and `uvicorn main:app` starts with a health endpoint.

### Phase 1: Extraction and validation
- `prompts/extract_prompt.txt` from section 8.
- `extract.py`: call the model, then parse JSON robustly. Strip code fences. If parsing fails, retry once. If it still fails, return an error object, not a guess.
- Validate against the schema in section 8 with pydantic. A missing field becomes null, not a made-up value.
- Save raw outputs to `eval/results/` when run from the eval harness.
- `scripts/try_one.py`: take one image path, resize it, make one real model call using the image request format in section 8, then print the raw model text and the seconds taken. Show readable errors for a missing key, 401, timeout and empty response. Save nothing except an optional raw output file under `eval/results/`.
- **Done when:** unit tests pass for the parser using fake model text, including fenced JSON, extra text around JSON, and broken JSON, and `try_one.py` runs.
- **STOP.** The human runs `try_one.py` on one real prescription and reports whether the image call works. If the call fails, report the exact error. Do not switch models or invent a workaround.

### Phase 2: Matching, timing and status
- `scripts/load_medicines.py`: load a CSV with columns `brand_name, generic_name, strength, use` into SQLite. The human provides the CSV. Do not download datasets.
- `match.py`: RapidFuzz against brand and generic names. Thresholds from `config.py`. Return best match, score, and any second candidate within 5 points (starting guess), so the caller can show both.
- `timing.py`: the dictionary in section 8. Unknown code returns the raw text and a flag.
- `status.py`: the rule in section 8.
- **Done when:** pytest passes on synthetic strings, including: exact match, misspelling, score below review threshold, two close candidates, null name, known and unknown timing codes.

### Phase 3: Evaluation harness
- `eval/run_eval.py`, one command, reads images from `tests_local/prescriptions/` and answers from `eval/expected.csv`.
- Two modes on the same model and images:
  - `--mode baseline`: prompt from `prompts/baseline_prompt.txt` (same JSON fields, no rules), no matching, no decoder, no flags. Baseline rows are always unflagged.
  - `--mode pipeline`: the full pipeline.
- Pair and score rows exactly as described in section 8 ("Scoring and pairing").
- Scoring follows `eval/scoring_rules.md`. **Do not decide scoring rules yourself.** Create a template listing the open questions (brand vs generic equivalence, missing strength, flagged-but-correct rows) and leave them for the human.
- Per item, assign one of: **correct**, **wrong but flagged**, **wrong and not flagged** (dangerous).
- Output: name accuracy, timing accuracy, unclear rate, dangerous-error count, seconds per image, printed vs handwritten reported separately. Write a CSV and a markdown table.
- Dataset split: rows in `expected.csv` carry a `group` column, `A` or `B`. Group B only runs with an explicit `--final` flag, and the script prints a warning that B must be used once.
- Never print or invent sample numbers.
- **STOP.** The human runs it on 10 prescriptions and decides whether to continue.

### Phase 4: FastAPI service
- `POST /read`: accepts an image upload, rejects files over a size limit, and checks that the file is an image.
- Pipeline: rotation fix, resize, (quality check if built), model call, match, decode, status.
- Response: JSON with the rows (name, strength, timing in plain words, duration, status, match candidates, reason for the flag) and the safety banner text.
- No photo is written to disk. No medicine names in logs.
- Timeouts and clear error messages.
- Serve `static/` and `GET /health`.
- **Done when:** pytest with a synthetic image and a mocked model call passes.

### Phase 5: Plain mobile page
Build it functional first, with no styling beyond layout.
- `<input type="file" accept="image/*" capture="environment">` for the camera, and a second input without `capture` for the gallery. Do not use `getUserMedia` (it needs HTTPS).
- Resize and compress in the browser with canvas before upload: longest side 1600 px, JPEG quality 0.8 (starting guess, read from one constant).
- States: home, loading (with the photo thumbnail), result, error with retry.
- Result: safety banner at the top, thumbnail (tap to zoom), then one row per medicine with a status word.
- Unreadable words are shown as a visible gap labeled "Could not read".
- **Done when:** it works on a real phone on the same Wi-Fi as the laptop, with no console errors, and the page assets are small (starting guess: under 200 KB total, excluding the user's photo).

### Phase 6: Design pass
Apply section 7 exactly. Change CSS and markup only. Do not change behavior.
- **Done when:** it passes the checks at the end of section 7, on a real phone.

### Phase 7: Photo quality check (add-on 1)
- In `clean.py`: blur (variance of the Laplacian), brightness, and size checks, with thresholds in `config.py` (starting guesses).
- If it fails, the API returns a retake message and the page shows it. No model call is made.
- **Done when:** unit tests pass on generated blurry, dark and small images.

### Phase 8: Correction table (add-on 2)
- Edit screen: tap a row, fix the name, save.
- `corrections.py` and table:

```sql
CREATE TABLE corrections (
    id INTEGER PRIMARY KEY,
    raw_text TEXT NOT NULL,
    corrected_name TEXT NOT NULL,
    times_confirmed INTEGER DEFAULT 1,
    verified INTEGER DEFAULT 0,
    created_at TEXT
);
```

- Store text only. No photo, no user ID.
- A correction is `verified` only if `corrected_name` exists in `medicines.db`. The human will decide any second rule. Leave a `TODO` in the code for it.
- When the model output matches a stored `raw_text`, show the `corrected_name` as a suggestion with the status **Check this**. Never replace the reading silently.
- **Done when:** tests cover saving, verification against the medicine DB, and suggestion display.

### Phase 9: Documentation
- README sections: problem, flow diagram (text or simple image), how to run in 5 steps, privacy notes, limits, disclaimer.
- Results table with `TBD` values and a note: "filled from `eval/run_eval.py` output."
- A "Limits" section: small test set, medicine list coverage, one model, free-tier dependency.
- Do not write numbers you have not seen produced by the harness.

---

## 7. Design brief (Phase 6)

**Concept:** a printed pharmacy slip that shows its uncertainty. The product's point is that it admits what it could not read, so make that visible.

### Do
- **Layout:** left-aligned rows separated by thin lines. No cards, no shadows. Corner radius 0 to 6 px.
- **Colors:** an off-white paper background, near-black ink, one accent color. Three status colors only: dark green (OK), amber (Check this), red (Unclear). Status always has a word too, not color alone.
- **Unreadable words:** a hatched or struck-through block labeled "Could not read". This is the signature element.
- **Status labels:** small stamp-style tags in plain text.
- **Fonts:** the system font stack (`system-ui, -apple-system, sans-serif`), or one self-hosted font file at most. Do not bundle Apple's San Francisco font.
- **Words:** plain and specific, for example "Could not read this word. Check with your pharmacist." The app name appears as "Trazo", set in lowercase or small caps, with no logo mark and no tagline.
- **Motion:** 150 to 200 ms fade or slide on rows appearing. Grey placeholder lines while loading, not a spinner.
- **Mobile details:** single column, tap targets at least 44 px, input text 16 px or larger, `100dvh` for full height, `env(safe-area-inset-bottom)` for the bottom bar, text contrast at least 4.5:1 for body text.
- **Motion rules:** animate only `transform` and `opacity`. Respect `prefers-reduced-motion`.

### Never
- Gradients, blur or glass effects, heavy shadows
- Big rounded cards
- Centered hero sections, feature grids, marketing copy
- Sparkle icons, emojis, "AI-powered" badges
- Friendly error text like "Oops! Something went wrong"
- Dark mode
- Icon libraries, UI kits, or any external stylesheet or script

### Screens (four)
1. **Home:** one camera button, one gallery button, one line saying what Trazo does, one line with the safety notice.
2. **Loading:** the photo thumbnail plus grey placeholder rows.
3. **Result:** safety banner, thumbnail, rows.
4. **Edit (Phase 8):** a text field with the model's reading and the correction field, plus Save and Cancel.

The human will provide sketches for these later. Until then, follow the layout notes above. Do not invent extra screens.

### Design check
- Compare against the "Never" list line by line and report any violations.
- Test at 360 px wide and at 430 px wide.

---

## 8. Specifications

### Extraction JSON (schema)

```json
{
  "medicines": [
    {
      "name": "string or null",
      "strength": "string or null",
      "timing_code": "string or null",
      "duration": "string or null",
      "confidence": 0.0,
      "unclear": false
    }
  ],
  "notes": "anything unreadable on the page"
}
```

### `prompts/extract_prompt.txt` (starting version, the human will tune it)

```
You are reading a photo of a doctor's prescription.
Return only JSON in exactly this format, with no other text:
{"medicines":[{"name":null,"strength":null,"timing_code":null,"duration":null,"confidence":0.0,"unclear":false}],"notes":""}

Rules:
- List only medicines that are written on the page.
- If a word is not readable with high certainty, set "unclear" to true and "name" to null.
- Never replace an unreadable word with a similar real medicine name.
- Copy the timing code exactly as written (for example 1-0-1, BD, SOS). Do not translate it.
- Use null for any field you cannot read.
- Do not add medicines that are not on the page.
- "notes" should mention anything on the page you could not read at all.
```

### `prompts/baseline_prompt.txt`

```
Read this prescription. Return only JSON in this format:
{"medicines":[{"name":null,"strength":null,"timing_code":null,"duration":null}]}
```

- The baseline has the same fields but none of the rules: no "never guess", no `unclear` field, no matching, no decoder. So it can never flag a row. The README must state this: the baseline is a JSON-formatted plain prompt, not a free-text chatbot.

### Status rule

A row is **OK** only if all are true:
- The model did not set `unclear`.
- The database match score is at or above the accept threshold (90, starting guess).
- The timing code is in the dictionary.
- No second medicine name scores within the close margin of the match.

Score between review and accept thresholds (70 to 90): **Check this**, and show "Did you mean ...?". Below 70, or `name` null, or `unclear` true: **Unclear**. Always include a short reason with every flag.

### Timing dictionary

```python
TIMING = {
    "1-0-1": "Morning and night",
    "1-1-1": "Morning, afternoon and night",
    "1-0-0": "Morning only",
    "0-0-1": "Night only",
    "0-1-0": "Afternoon only",
    "OD":  "Once a day",
    "BD":  "Twice a day",
    "TDS": "Three times a day",
    "QID": "Four times a day",
    "SOS": "Only when needed",
    "HS":  "At bedtime",
    "AC":  "Before food",
    "PC":  "After food",
}
```

- Unknown or null codes are flagged and shown exactly as written. Never guess a meaning.

### Image request format (untested for this model)

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url",
         "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ],
}]
```

- This is the common OpenAI-style format, used with `temperature=0`. It has not been confirmed for GLM 5.3 Flash. Phase 1 tests it.

### Scoring and pairing (evaluation harness)

Proposed rules. The human can change them in `eval/scoring_rules.md`. Where that file is silent, use these.

- Fields that count toward an item being correct: name and timing, plus strength or duration only if `scoring_rules.md` says so. Timing is compared after the same normalization as the decoder (strip, uppercase).
- `names_equal(a, b)`: implement as one function using the equivalence rules in `scoring_rules.md`. Until the human provides them, compare after lowercasing and removing spaces and punctuation, and mark it `TODO`.
- Pairing, per image:
  1. Pair model rows with answer-key rows one to one by name similarity (RapidFuzz), highest first, using a pairing threshold from `config.py` (starting guess 60).
  2. Leftover model rows with `unclear` true pair with leftover key rows in reading order (top to bottom).
  3. Leftover key rows with no model row are **missed**. Count them as wrong and not flagged, and report them as a separate sub-count.
  4. Leftover model rows that are not `unclear` are **extra** (invented). Count them as wrong.
- Outcome per item: **correct** (all counted fields right) or **wrong**. A wrong item is **flagged** if its status is not OK, and **dangerous** otherwise. Baseline rows are never flagged, so every wrong baseline item is dangerous.
- Report separately: missed medicines, extra medicines, and dangerous errors in each mode.
- Save every pairing decision in the results CSV so the human can audit it.

### `expected.csv` columns (the human fills them)

`image_file, group, kind, medicine_name, strength, timing_code, duration`

- `group`: A or B. `kind`: printed or handwritten. One row per medicine.

---

## 9. Testing

- `pytest` covers parsing, matching, timing, status, quality check, corrections, and the API (with the model call mocked).
- Tests use synthetic strings and generated images only. No real prescriptions.
- Do not hit the real model API in automated tests.
- Report test results honestly, including failures.

---

## 10. Reporting format after each phase

1. What you built (a few lines).
2. How to run it (exact commands).
3. What is untested or unverified.
4. Assumptions you made.
5. What you need from the human next.

No long summaries, no praise, no claims about accuracy.