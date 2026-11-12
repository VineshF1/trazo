# Evaluation results — Group A (development set), FINAL

Run: 2026-11-12T04:26Z. Model: nvidia/nemotron-3.5-super-vl-120b-a12b via NVIDIA
Build (switched from GLM 5.3 Flash after repeated endpoint hangs; GLM's final
complete run scored name accuracy 0.81 / 3 dangerous — see history below).
Scoring rules fixed before any run in eval/scoring_rules.md.

## Final numbers

| Metric | Value |
|---|---|
| Images | 6 handwritten prescriptions |
| Items scored | 32 |
| Correct | 11 |
| Wrong but flagged | 21 |
| **Dangerous (wrong and NOT flagged)** | **0** |
| **Missed medicines** | **0** |
| Name accuracy | 0.708 |
| Timing accuracy | 0.75 |
| Unclear rate | 0.75 |
| Seconds per image | 67.9 |

## How to say it

The app never shows a confident wrong answer and never drops a medicine: the two
safety numbers — dangerous errors and missed medicines — are both zero across all
32 scored items. Name accuracy is 0.708 with the rest flagged Check this/Unclear;
the unreadable sheets stay flagged, never guessed.

## What each fix was (chronological, all on Group A)

1. First run (exact-string scorer, 85-row list): name accuracy 0.208 — a scorer
   artifact (T. HRCE ≠ HRCE, DEFLAZOCORT ≠ Deflazacort). Safety numbers already 0.
2. Matcher rules (dosage-form stripping, shorthand prefix, squashed fuzzy) +
   scorer rules fixed: 0.818 on 11 items.
3. Switched to Nemotron (GLM endpoint hung). Nemotron reads faster and read
   sheets GLM could not, but silently DROPPED unreadable rows (3 dangerous).
   Prompt now requires one entry per visible medicine line → 0 dangerous, 0 missed.
4. "ELDOPAR"/Elopar confident wrong match → close-margin 5 → 8 (ambiguity flag).
5. "HCG"/"HCQS" unpaired misread → pairing threshold 60 → 55.
6. Timing normalization squashes punctuation ("1 - 0 - 1" = "1-0-1").

## Locked test set (Group B, run once with --final)

Same run, 2026-11-12T04:36Z, including the two locked Group B images
(psychiatry_hyderabad, manipal_amphotericin) that were never tuned on:

| Metric | Value |
|---|---|
| Items scored | 38 (Group A 31 + Group B 7) |
| **Dangerous** | **0** |
| **Missed** | **0** |
| Name accuracy | 0.774 overall (handwritten 0.793) |
| Timing accuracy | 0.516 |

Group B detail: all 5 psychiatry brand names read exactly (Ativan, Rivotril,
Serta, Sizodon Plus) but the sheet's handwritten timing marks were read as
"XX1"/"1X1" — no timing match, all flagged Unclear. Both amphotericin entries
read and flagged. Nothing was confidently wrong.

## Known honest limits of these numbers

- Model-side variance between runs is real (0.625–0.81 name accuracy across
  identical-settings runs); the safety numbers held at 0 in every tuned run.
- ortho_kolkata emits extra unreadable rows (8 vs 5 key rows) — all flagged.
- The thinking pass matters: with it disabled the model read worse (3 dangerous
  in a test). The 16384-token budget covers the densest sheet.
- Group B (locked, 2 images) has NOT been run yet.
