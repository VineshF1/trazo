# Prescription Reader

Project plan for a college mini project and GitHub portfolio repo. Everything marked "starting guess" must be tuned on your own data.

---

## 1. Project summary

- **What:** A mobile-first web app. The user takes a photo of a doctor's prescription on their phone, in Chrome or another mobile browser. It returns a list of medicine name, strength, when to take, and for how many days.
- **Core rule:** It never guesses. Anything it cannot read clearly is flagged instead of filled in.
- **Safety banner on every result:** "This is a reading aid, not medical advice. Confirm with your pharmacist."
- **One-line pitch:** A prescription reader that is honest about what it cannot read, with measured accuracy to prove it.

### Basics

- App name: Trazo (Spanish for pen stroke).
- Delivery: a mobile web app opened in Chrome or another mobile browser (section 7). Not a native app.
- Inference: GLM 5.3 Flash (`z-ai/glm-5.3-flash`) on NVIDIA Build, free API.
- Presentation: PPT plus a live demo on a phone.
- The project will also be published on GitHub under your name.
- A build prompt for an AI coding agent is in `trazo-build-prompt.md`.

---

## 2. Problem and users

- **Problem:** Doctor handwriting and short forms are hard for patients to read. Wrong dose or skipped medicines is a real risk.
- **Gap:** Many tools show confident output even when the reading is wrong.
- **Primary users:** Patients and family members who cannot read the handwriting, using their phone.
- **Secondary users:** Caregivers handling medicines for elderly parents.
- **Not the target:** Doctors and pharmacists.

---

## 3. What makes the project stand out

Features do not make this interesting to lecturers. Evidence does. In priority order:

1. **Baseline vs pipeline comparison:** same prescriptions run through GLM with a plain prompt, and through your full pipeline (prompt rules, matching, timing decoder, flags). Same model, two setups. Show both in one table.
2. **Dangerous-error count:** wrong answers the app did NOT flag. The headline safety number.
3. **Live failure demo on a phone:** photograph a messy prescription, and the app marks the unreadable word visibly instead of guessing.
4. **Error breakdown:** failures grouped by cause (messy handwriting, short forms, brand confusion, bad photo), and what you would fix next.
5. **Photo quality check:** "retake this photo" on blurry or dark images. Cheap and visible in a demo.
6. **Safe self-improvement:** a verified-correction table. Fix a wrong row, upload again, and see the app suggest the fix with a "Check this" flag.
7. **One-command evaluation:** anyone can reproduce your numbers.

---

## 4. Scope

### Core (finish this first)

- Mobile-first web page: camera capture or gallery pick, photo preview
- Image cleanup and resize
- Extraction to JSON with GLM 5.3 Flash
- Medicine database matching
- Timing code decoder
- Flags for unclear, low-match and unknown-code rows
- Safety banner
- Baseline vs pipeline comparison
- Accuracy test on 20 to 30 prescriptions

### Add-ons (only after the core works, in this order)

1. Photo quality check
2. User correction step and correction table (experimental)
3. Telugu or Hindi explanations (decide at the end)

### Out of scope

- Diagnosis or medical advice
- Dose suggestions or changes
- Storing patient data or photos
- Claims of clinical safety
- Native mobile app

---

## 5. System flow

1. User takes a photo (or picks one from the gallery) on the phone.
2. The browser resizes and compresses the photo, then uploads it.
3. The server fixes photo rotation (EXIF), then runs the photo quality check (add-on). If bad, ask for a retake.
4. OpenCV cleans the image.
5. GLM 5.3 Flash returns JSON.
6. Each name is matched against the medicine database.
7. Correction table is checked for known bad readings (add-on; suggestion only, always flagged).
8. Timing codes are decoded.
9. Result list is shown with statuses: OK, Check this, Unclear.
10. Photo is deleted. Only text corrections (if the user makes any) are saved.

---

## 6. Tech stack

| Part | Tool | Notes |
|---|---|---|
| Language | Python | One language for the backend |
| Image cleanup | Pillow + OpenCV | Pillow fixes rotation; OpenCV cleans |
| Vision model | GLM 5.3 Flash on NVIDIA Build | Free key, OpenAI-compatible API |
| API client | `openai` Python package | Set base URL to NVIDIA's endpoint |
| Backend | FastAPI | One endpoint, `POST /read`; also serves the static page |
| Frontend | Static HTML + CSS + JavaScript | No framework, no build step |
| Matching | RapidFuzz | Fuzzy text matching |
| Database | SQLite | Medicines and corrections |
| Testing | pandas + CSV | Accuracy scripts call the Python functions directly, not the UI |

---

## 7. Mobile web app and UI

### Delivery

- A web page opened in Chrome or another mobile browser. Optimized for the phone, not a native app.
- **Camera:** use `<input type="file" accept="image/*" capture="environment">`. On a phone it opens the camera app directly.
- **Gallery:** add a second button without `capture` so users can pick an existing photo.
- **Why not live video preview:** browsers only allow it on HTTPS pages. A file input works without that, which avoids setup trouble during development.

### Upload handling

- **Resize in the browser before upload.** Phone photos are often several MB, which is slow on mobile data. Starting guess: longest side about 1600 px, JPEG quality about 0.8. Tune on your own images.
- **Fix rotation on the server.** Phone photos can carry rotation info that some libraries ignore, so the prescription arrives sideways. Use Pillow's `ImageOps.exif_transpose` before OpenCV.
- **Do not store photos.** Process in memory and delete.

### Design direction

**Idea:** the product's point is that it admits what it could not read. Make that the visual identity: a printed pharmacy slip that shows its uncertainty.

- **Layout:** left-aligned rows separated by thin lines, like a receipt or prescription slip. No cards, no shadows, small corner radius (0 to 6 px).
- **Colors:** an off-white paper background, near-black ink, and one accent color. Three status colors only: dark green for OK, amber for Check this, red for Unclear. Status always has a word too, not color alone.
- **Unreadable words:** shown as a visible gap, such as a hatched or struck-through block labeled "Could not read". This is the signature element of the app.
- **Status labels:** small stamp-style tags. Text stays plain and clear.
- **Fonts:** one serif for headings and one clean font for data, or only the system font (`system-ui, -apple-system, sans-serif`) and let layout carry the design. Web fonts add load time on mobile data, so self-host one small file at most. Do not bundle Apple's San Francisco font.
- **Words:** plain and specific. "Could not read this word. Check with your pharmacist." Not "Oops!".
- **Motion:** 150 to 200 ms fade or slide on rows appearing. No looping animations. Grey placeholder lines while the model works, not a spinner.
- **Icons:** none, or a few simple ones you draw yourself in one stroke style.

**Avoid (reads as AI-generated):**
- Purple-to-blue gradients
- Big rounded cards with soft shadows
- A centered hero with a gradient button
- Sparkle icons, emojis, "AI-powered" badges
- One default font for everything
- A features grid or any marketing copy
- Friendly error text like "Oops! Something went wrong"

### The four screens (sketch these on paper later)

1. **Home:** one camera button, one line saying what it does, one line with the safety notice. No hero, no extras.
2. **Loading:** the photo thumbnail plus placeholder rows.
3. **Result:** photo thumbnail (tap to zoom), safety banner at the top, then the rows.
4. **Edit:** tap a row, fix the name, save. This feeds the correction table.

### Performance and smoothness rules

- Animate only `transform` and `opacity`. Never animate width, height, blur or shadows.
- No blur effects and no heavy shadows. They load the phone's graphics chip.
- Keep the page light. Measure seconds from photo to result on mobile data and report it in the README.
- Use `100dvh` for full-screen height and `env(safe-area-inset-bottom)` so the bottom bar clears the home indicator.
- Text size 16px or larger on inputs, or iPhones zoom in.
- Large tap targets, single column.
- Respect `prefers-reduced-motion`.
- Text contrast stays high. Aim for the common 4.5:1 guideline for body text. This is a medicine app, so legibility beats style.
- Test on at least 2 real phones. Chrome's device mode is fine for layout, but the camera needs a real phone. With an Android phone connected by USB, `chrome://inspect` lets you check performance on the device.

### Build order

1. Test the whole system first (core, then accuracy test).
2. Plain mobile UI: rows, statuses, loading and error states. It must work and be readable.
3. Apply the design direction above.
4. Cap the whole UI at about 3 days. If time is short, cut polish, not the accuracy test.

---

## 8. Data

### Prescriptions

- First check: 10 prescriptions (quick feasibility test).
- Final: 20 to 30. Numbers on this size are rough. Say "tested on N prescriptions" in the README and do not call the result proven.
- Sources: family, friends, your own past prescriptions.
- **Consent:** tell each person their photo will be sent to an online AI service for processing, and get a yes after they know that.
- Blur names, phone numbers and addresses.
- Mix them: printed and handwritten, clean and messy. Aim for at least 8 to 10 in each group you want to report separately.
- **Split the set:**
  - Group A (development): used to tune prompts, thresholds and corrections.
  - Group B (locked, about 8 to 10): used only once for the final reported numbers.

### Answer key

- Someone who can read the handwriting must confirm every answer in `expected.csv`: a pharmacist, the patient, or a family member who knows the medicines.
- If you cannot read a prescription yourself, an unchecked key makes your accuracy numbers wrong without anyone noticing.

### Medicine list

- Start from the medicines actually on your test prescriptions, then add common ones, up to about 100 to 300 in total: brand name, generic name, strength, use.
- A public dataset can help (search Kaggle for an Indian medicine dataset). Do not commit it to your repo. Link to it and provide a download script.
- Load into SQLite.
- **Report coverage:** how many medicines on your test prescriptions are in your list. If a medicine is missing from the list, matching fails, and that is not the model's fault. Do not claim the app "knows Indian medicines" if it knows 200.

### Data warning

- If you cannot get about 20 real prescriptions, the project has no accuracy proof. Decide early.

---

## 9. Core components

### 9.1 Extraction JSON

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

### 9.2 Prompt rules

- Return only JSON, nothing else.
- If a word is not readable with high certainty, set `unclear: true` and `name: null`.
- Never replace an unreadable word with a similar real medicine.
- Copy the timing code exactly as written.
- Do not add medicines that are not on the page.
- The model's `confidence` is a weak signal only. Do not show it to users as "accuracy".
- Write the prompt, test it on 5 prescriptions by hand, and read the errors before writing app code.

### 9.3 Baseline prompt (for the comparison)

- A plain prompt that asks for the same JSON fields, with no rules (no "never guess", no `unclear` field), no matching and no decoder. It can never flag a row.
- Same model, same images. Only the setup differs.
- State in the README: the baseline is a JSON-formatted plain prompt, not a free-text chatbot.

### 9.4 Matching (starting guesses, tune on Group A)

- Score above 90: accept the match.
- Score 70 to 90: show "Did you mean ...?" and flag the row.
- Score below 70: mark "not found" and flag the row.
- If two medicines score close to each other, show both and flag the row. Never pick silently.
- Compare against both brand and generic names.

### 9.5 Status rule (combine several checks)

A row is **OK** only if all are true:
- Model did not set `unclear`.
- Database match score is above the accept threshold.
- Timing code is in the dictionary.
- No second medicine name scores close to the match.

Otherwise the row is **Check this** or **Unclear**.

### 9.6 Timing decoder

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

def decode(code):
    if code is None:
        return None, True            # flag
    key = code.strip().upper()
    if key in TIMING:
        return TIMING[key], False
    return code, True                # unknown code: show raw, flag
```

- Any code not in the dictionary is flagged and shown exactly as written. Never guess a meaning.

### 9.7 Photo quality check (add-on 1)

- Detect blur (variance of Laplacian in OpenCV is a common method), low brightness, and small image size.
- If the photo fails, show "Retake this photo" instead of reading it.
- Thresholds are starting guesses; tune them on your own photos.

---

## 10. Safe self-improvement: verified-correction table (add-on 2)

### What it is

- The app learns from user corrections, not from its own readings.
- It does NOT retrain the model. It improves the code and data around the model.

### What it must not do

- Do not learn from the model's own output. Mistakes would repeat and compound.
- Do not store photos. This keeps the privacy promise.
- Do not silently replace a reading. A learned suggestion always stays flagged "Check this".

### How it works

1. App shows a result. The user taps a row and fixes any wrong name.
2. Save only text: `raw_text` (what the model read) and `corrected_name` (what the user entered). No photo, no user ID.
3. A correction becomes "verified" only if the corrected name exists in your medicine database. Add one more rule of your choice (for example, confirmed by more than one correction).
4. Later, if the model outputs a `raw_text` found in the table, suggest the `corrected_name` with a "Check this" flag.

### Table schema

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

### How to prove it works

- Collect corrections using Group A only.
- Measure accuracy on Group B before and after adding the table.
- Report both numbers. If there is no improvement, say so.

### Weak points

- User corrections can be wrong. Keeping every learned item flagged limits the damage.
- With 20 to 30 prescriptions, the table will be tiny and the gain may be too small to measure. Present it as a working design shown in a live demo, not a proven result, and say that out loud.

---

## 11. Safety design

- Safety banner on every result.
- Flags on every unclear, low-score, unknown-code or close-match row.
- No dose suggestions or changes.
- Do not store uploaded photos. Process in memory, delete after.
- Do not log medicine names with user identity.
- Show the original photo next to the result so the user can compare.
- Do not claim "safe", "accurate" or "ready for patients". Say "student project with measured accuracy".

---

## 12. Testing plan

### Write before testing

- `eval/scoring_rules.md` with exact rules for what counts as correct. For example:
  - Is "Dolo 650" correct if the key says "Paracetamol 650 mg"?
  - Does a missing strength count as wrong?
  - Does a flagged row with the right name count as correct?
- Your targets, such as the maximum number of dangerous errors you will accept.
- If you set these after seeing results, you will bend them toward better numbers.

### Metrics (define precisely in your README)

- **Name accuracy:** correct medicine names / total medicines in the test set.
- **Timing accuracy:** correct timing / total.
- **Unclear rate:** items flagged as unclear / total items.
- **Three-group score per item:**
  - Correct
  - Wrong but flagged (acceptable)
  - Wrong and NOT flagged (dangerous)
- **Dangerous-error count:** the third group. The most important number.
- **Seconds per image**, and seconds from photo to result on a phone over mobile data.
- Report printed and handwritten separately.

### Experiments to run

1. **Feasibility check:** 10 prescriptions through GLM 5.3 Flash. Decide whether to build the app.
2. **Baseline vs pipeline:** plain prompt vs full pipeline on Group A.
3. **Correction table test (if built):** Group B before and after.
4. **Final run:** Group B once, with the chosen setup. Report these numbers.

### Rules

- Never tune on Group B.
- Report failures. Hiding them lowers trust.
- Save raw outputs, model name, and test date.

### Decision after the feasibility check

- Mostly correct or flagged: build the app.
- Many wrong and not flagged: fix the prompt and flags before building anything else.
- Model fails on handwriting: report printed and handwritten separately, and say so honestly.

---

## 13. College presentation

### PPT outline

1. Problem: show a real messy prescription and ask the room if anyone can read it
2. Who it helps
3. System flow diagram
4. Live demo on your phone using the camera, including one caught failure, plus a backup screen recording in case the internet or API fails
5. Results: baseline vs pipeline
6. Dangerous-error count and how each case was handled
7. Error breakdown chart
8. Correction table demo (if built)
9. Safety and privacy design
10. Limits and what you would do next

### Likely lecturer questions

- **"Why not just upload the photo to a chatbot?"** Show the baseline vs pipeline table.
- **"How did you measure accuracy?"** Test set, locked Group B, answer key confirmed by someone who can read the handwriting.
- **"What if it reads the dose wrong?"** Flags, thresholds, pharmacist warning, dangerous-error count.
- **"Did you train a model?"** No. You used an API and improved the prompt, matching rules and data around it.
- **"Is it ready for real patients?"** No. It is not clinically validated and is a learning project.
- **"Is the sample size enough?"** No. It is a small test, and you say so.
- **"What would you do with more time?"** Larger test set, more models, pharmacist review.

### Habits

- Say the limits yourself before someone else asks.
- Do not show only your best prescription.
- Do not use "safe", "accurate" or "ready for patients" without a number or a qualifier.