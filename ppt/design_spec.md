<!-- ppt-master-schema: design-spec/v1 -->
# Trazo - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | Trazo |
| Canvas Format | PPT 16:9 (1280x720) |
| Page Count | 10 |
| Primary Language | en |
| Target Audience | Lecturers and classmates. Plain talk, no invented numbers, presenter is a student. |
| Communication Intent | Explain what Trazo does, how it works, how it stays honest and safe, and what is still missing. Accuracy and results slides wait for the first test run. |
| Desired Audience Outcome | They can state what Trazo does, that it flags what it cannot read, that accuracy measurement is designed but not yet run, and they know the safety boundary. |
| Core Message / Ask / Action | A prescription reader that is honest about what it cannot read, with measured accuracy to prove it. The measurement starts next. |
| Delivery Context | Presenter-led, click-paced animations, live phone demo, backup recording; deck also reviewed as a file. |
| Artifact Afterlife | Reviewed as a file and archived. |
| Reading Mode | balanced |
| Content Strategy | Balanced. Facts only from the project sources. [FILL] placeholders stay visible for the presenter to replace. Slides 9-10 of the source prompt (accuracy method, results) are held until eval/run_eval.py produces real numbers. |
| Design Style | Printed pharmacy slip. Off-white paper, near-black ink, thin rules, small corners (0-6 px), no gradients, no glass, no heavy shadows, no big rounded cards. One accent. Status colors only on status words, word always written. |
| AI Image Acquisition Path | Not applicable. Real app screenshots and a presenter-supplied photo only. |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled - one script per page, 3 to 5 plain sentences, about 40 seconds |
| Custom Animations | enabled - two motifs (stamp zoom, wipe-from-left), fade-wipe entrances, on-click pacing, slide 6 static. Per-page plan in animations sidecar. |
| Narration Audio | disabled - workflow default |
| Created Date | 2026-11-07 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 x 720 |
| viewBox | `0 0 1280 720` |
| Margins | 72 px on all sides |
| Content Area | 72,72 to 1208,648 |

## III. Visual Theme

### Theme Style

- **Mode**: narrative
- **Visual style**: editorial
- **Theme**: A printed pharmacy slip, used as a presentation. Off-white paper field, near-black ink, thin full-width rules, rectangular boxes with 4 px corners, one blue accent, status words carrying their semantic colour as text plus a thin border chip. Everything left-aligned. Nothing decorative.
- **Tone**: Plain, specific, unhurried. No marketing voice. No claim the project cannot back.

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FAF9F5 | Every page, paper |
| Panel | #F3F1EA | Screenshot mounts only |
| Primary | #171715 | Headlines, rules, table borders, image frames |
| Accent | #1D4ED8 | One highlighted element per page; pen stroke; links |
| Positive | #1E6B3A | Status word OK only |
| Warning | #7A5200 | Status word Check this only |
| Negative | #B3261E | Status word Unclear only; hard-to-read outlines |
| Body text | #171715 | Body copy and data |
| Secondary text | #4A4843 | Captions, annotations, FILL placeholders |
| Divider | #D9D6CF | Hairlines, table inner borders, dashed frames |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | Plain workhorse sans, print-slips and forms | Arial | Arial | sans-serif |
| Body | Same family for the whole deck, one clean character | Arial | Arial | sans-serif |
| Label | Same family, spacing used instead of a second face | Arial | Arial | sans-serif |

- **Title stack**: Arial, sans-serif
- **Body stack**: Arial, sans-serif
- **Label stack**: Arial, sans-serif

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Display | 120 |
| Title | 48 |
| Subtitle | 32 |
| Body | 27 |
| Tag | 18 |
| Brand | 28 |

## V. Layout Principles

### Deck-wide Direction

- **Headline style**: Title Case bold; the lowercase trazo wordmark styling applies to the small brand strip on every slide, with the wordmark display size on the cover.
- **Hierarchy direction**: headline, then the page's few points, then the boundary line.
- **Composition tendency**: left-aligned everything; hairline rules to separate; thin-bordered boxes with 4 px corners; no large rounded cards; no shadows; white space kept open.
- **Cross-page continuity**: brand strip top ("trazo" left, page number right) under a 1 px rule; 48 px headline; body 27 px; one accent element per page; status chips recur where status is discussed.
- **Spacing posture**: open. Density only on the tech-stack table and the flow diagram.
- **Spacing anchors**: margin 72 px; brand rule at y=100; headline baseline y=170; body leading 44 px; content bottom edge 640 px.

## VI. Icon Usage Specification

- **Primary bundled library**: tabler-outline
- **Stroke Width**: 2

| Icon Path | Suitable Scenarios |
| --- | --- |
| tabler-outline/camera | Take-photo action on the flow diagram |
| tabler-outline/eye-off | The unreadable hatch block |

## VII. Visualization Reference List

| Page | Family | Template | Usage |
| --- | --- | --- | --- |
| P06 | table | stack_table | Plain two-column part/tool table, six rows, thin rules |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Image pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| app-home.png | 480x844 | 0.57 | The home screen of the running app | Screenshot | Phone screen, the two actions and the safety note | no-crop | user | Existing | Captured from the local server via headless Chrome | none | local |
| app-result.png | 390x844 | 0.46 | The result screen with one OK row and one Check-this row | Screenshot | Result page with status words visible | no-crop | user | Existing | Synthetic prescription read by the live app | none | hero_page |
| app-retake.png | 390x844 | 0.46 | A caught failure: the photo could not be read | Screenshot | Failure screen with the retake message and actions | no-crop | user | Existing | Blank-photo 422 from the live app | none | local |
| rx-blur.png | 800x600 | 1.33 | A blurred, consented real prescription | Photo | Hand-held phone photo, blurred, one page | no-crop | user | Needs-Manual | Real prescription, consented | none | hero_photo |

## IX. Content Outline

### Part 1: The setup

#### Slide 01 - Title

- **Audience move**: arrive, learn the name and the one-line promise, see where the presenter sits.
- **Relationships**: name, pitch, presenter details, the meaning of the name.
- **Composition**: left-aligned wordmark with an accent pen-stroke line under it; pitch beneath; the meaning line last.
- **Title**: trazo
- **Core message**: The one-line pitch, said once, plainly.
- **Content**: Wordmark "trazo". Pitch: "A prescription reader that is honest about what it cannot read, with measured accuracy to prove it." Meaning line: "Trazo means pen stroke in Spanish."
- **Motion suggestion**: wordmark wipes from left; pen stroke wipes from left; pitch fades; presenter line fades.

#### Slide 02 - The problem

- **Audience move**: feel the problem before any solution talk.
- **Relationships**: the photo is the argument; one question; two short lines of consequence.
- **Composition**: large framed photo slot left with a marked [FILL] state; question and two lines right.
- **Title**: The problem
- **Core message**: Reading a prescription is genuinely hard, and a miss has consequences.
- **Content**: Frame: real prescription photo (anonymized public-collection image, patient details blurred; `rx-blur.png`). Caption: "This is a real prescription." Lines: "Doctor handwriting and short forms are hard to read." / "A wrong dose or skipped medicine is a real risk."
- **Motion suggestion**: the question and the two lines fade in, one per click; red hard-to-read outlines belong to the real photo and are added with it.

#### Slide 03 - Who it helps, and the gap

- **Audience move**: pin the user and sharpen why this is not just another reader.
- **Relationships**: users on the left, the gap on the right, a divider between.
- **Composition**: two text columns with a vertical hairline; headings 32; lines 27.
- **Title**: Who it helps, and the gap
- **Core message**: It is for people holding a phone, not clinicians; the gap is false confidence.
- **Content**: "Who it helps": "Patients and family members using a phone." / "Caregivers managing medicines for elderly parents." / "Not for doctors or pharmacists." "The gap": "Most tools show confident output even when the reading is wrong." / "Trazo shows what it could not read."
- **Motion suggestion**: lines fade in one per click.

### Part 2: The product

#### Slide 04 - What Trazo does

- **Audience move**: from words to the real result screen.
- **Relationships**: three plain points on the left; the real result screen on the right; the exact safety banner text.
- **Composition**: text column left with the banner in a thin box; framed screenshot right.
- **Title**: What Trazo does
- **Core message**: It lists the medicines and marks everything it could not read.
- **Content**: "Reads a prescription photo." / "Shows medicine, strength, timing, duration." / "Marks every unclear word instead of guessing." Banner, exact: "This is a reading aid, not medical advice. Confirm with your pharmacist."
- **Motion suggestion**: the three points fade in one per click.

#### Slide 05 - How it works

- **Audience move**: hold the six-step pipeline in one glance, each step self-describing.
- **Relationships**: six boxes left to right, name and one-line job in each box, arrows between, photo's journey as the frame.
- **Composition**: six rectangular boxes in one row with accent arrows and step boxes; three status chips as a legend beneath; the storage line under all.
- **Title**: How it works
- **Core message**: Photo in, status out; the photo never stays.
- **Content**: Boxes: "Photo - camera capture" / "Clean, resize - fix tilt, size" / "Vision model - reads the words" / "Match to list - finds medicine" / "Decode timing - 1-0-1, BD, SOS" / "Result - rows on screen". Legend: "OK" (green) / "Check this" (amber) / "Unclear" (red). Line: "The photo is processed in memory and deleted. It is not stored."
- **Motion suggestion**: arrows wipe then boxes wipe, one click per stop; a dot travels the row once on the last click.

#### Slide 06 - Tech stack

- **Audience move**: see that it is plain, free tooling, no training.
- **Relationships**: part and tool in a two-column table.
- **Composition**: thin-ruled table; one accent line beneath. No animation on this page.
- **Title**: Tech stack
- **Core message**: The work is in the rules, not in a trained model.
- **Content**: Rows: "Browser - HTML, CSS, JavaScript" / "Server - Python, FastAPI" / "Image handling - OpenCV, Pillow" / "Name matching - RapidFuzz" / "Storage - SQLite" / "Model - Ready-made vision model, via API". Line: "Free model API, no training. The accuracy work is in the prompt, matching rules and flags."
- **Motion suggestion**: none. A table is read, not played.

#### Slide 07 - Safety and privacy design

- **Audience move**: trust the boundaries before trusting numbers.
- **Relationships**: five points that each close a door; the OK tag lands when the four checks are named.
- **Composition**: five stack lines; a green OK chip anchored to the second line.
- **Title**: Safety and privacy design
- **Core message**: Honesty and privacy are design decisions, not promises.
- **Content**: "It never fills an unreadable word - it flags it instead." / "A row reads OK only after four checks pass." (green OK stamp; the four checks are spoken in the notes and listed in the QA sheet, not shown on the slide) / "Warning on every result: a reading aid, not medical advice." / "No photo is stored, ever." / "No dose advice or diagnosis."
- **Motion suggestion**: five points fade in one per click; the OK tag stamps after the second.

#### Slide 08 - Live demo

- **Audience move**: from slides to the real phone.
- **Relationships**: three real screens left to right: home, result, caught failure; the failure carries the hatch motif.
- **Composition**: three framed screenshots in a row with 27 px captions; demo line under the headline; backup note at the foot.
- **Title**: Live demo
- **Core message**: The refusal screen is part of the demo, not an exception to it.
- **Content**: Demo line: "Live demo on a phone, using the camera." Screenshots: "app-home.png - Home" / "app-result.png - Result" / "app-retake.png - Caught failure". Hatch block on the failure shot labelled "Could not read".
- **Motion suggestion**: shots fade left to right; the hatch block wipes from left over the failure shot.

### Part 3: The boundary

#### Slide 09 - Limits

- **Audience move**: say the limits before a lecturer asks.
- **Relationships**: five honest limits; the pending measurement is named, not hidden.
- **Composition**: five stack lines; the first one in accent because it is the active limit.
- **Title**: Limits
- **Core message**: Accuracy slides exist but wait for the first test run.
- **Content**: "Medicine list covers only [FILL: number] medicines." / "A name on the list is matched accurately; one off it stays Check this." / "It reads what is written; it does not check doses." / "The small list is the real limit - this is not a production system." / "No clinical validation - a learning project."
- **Motion suggestion**: lines fade in one per click.

#### Slide 10 - Next steps, and thanks

- **Audience move**: close by repeating the whole project in three lines, then open the floor.
- **Relationships**: what it does, how it stays honest, its boundary; then thanks, then questions.
- **Composition**: three short lines; a large "Thank you."; an accent "Questions?"
- **Title**: Summary
- **Core message**: Reads a photo, flags what it cannot read, warns on every result.
- **Content**: "Reads a prescription photo and lists each medicine." / "Flags every word it cannot read - it never guesses." / "Warns on every result: a reading aid, not medical advice." End: "Thank you."
- **Motion suggestion**: lines fade one per click; thank-you and questions land last.

## X. Speaker Notes Requirements

- **Content**: one spoken script per page in the presenter's voice, first person, 3 to 5 plain sentences, about 40 seconds per page; longer allowed where the boundary is discussed. Never read a bullet verbatim; never invent a number. Where a [FILL] placeholder stands, the note says the value will be read from the slide.
- **Total duration**: 8 to 10 minutes, presenter-led, click-paced animations, live phone demo after the methodology, backup screen recording.

- The three backup Q&A pages were removed from the deck at the presenter's request. Their answers live in `Trazo_QA_answers.md`, a separate off-screen sheet covering the chatbot, trained-model, and ready-for-patients questions plus other expected questions, all from built facts.
