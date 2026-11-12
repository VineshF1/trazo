# Scoring rules

**Status: decided 2026-11-12.** These rules were fixed after the first Group A run
and before any Group B run. `eval/scoring.py` implements them.

## Decided rules

1. **Name equivalence (`names_equal`).** Two names count as the same medicine when
   any of these holds, after lowercasing, dropping punctuation and merging spaces:
   - **Exact**: the same string (`"T. HRCE"` = `"HRCE"`, `"Dolo 650"` = `"dolo650"`).
     Leading dosage-form words (`T.`, `Tab`, `Cap`, `Syp`, `Inj`, ...) are stripped
     first — the form is not part of the name.
   - **Prefix (shorthand)**: one name is a prefix of the other, at least 3 characters
     (`"HCQ"` = `"HCQS"`, `"Pantop"` = `"Pantop DSR"`, `"Etoricoxib"` = `"Etoricoxib MR"`).
     Doctors abbreviate; the shorthand still names the same medicine.
   - **Fuzzy (word-order-insensitive) similarity >= 90**:
     `"5% Dextrose"` = `"Dextrose 5"`, `"DEFLAZOCORT"` = `"Deflazacort"` (the
     spelling the doctor wrote on the paper), `"EMESSET-MDS"` = `"Emeset MDS"`.
   - **Still wrong**: genuinely different reads (`"Rumaspas"` vs `"Rumaspab"`,
     `"REXPRAZOLE"` vs `"Rexazol"`). Those stay wrong-but-flagged.
   - Rationale: the metric measures "did the app read the right medicine", not
     "did it reproduce spelling", because the paper itself carries misspellings
     and shorthands. The rule set is applied identically to every group.

2. **Brand vs generic.** Not interchangeable: if the key says a brand and the model
   read a different medicine's generic, that is wrong. Same-string brand/generic
   rows score naturally.

3. **Strength.** Not scored. Too much of the strength on these sheets is smudged
   or abbreviated; scoring it would measure the paper, not the app.

4. **Duration.** Not scored, same reason.

5. **Timing.** Compared after uppercase + whitespace strip. `"BD"` = `"B.D."` counts
   as the same (punctuation dropped by the name-style squash is applied to the code
   too: `BD` vs `B.D.` -> `BD` = `BD`). An unknown or missing timing is simply not
   correct.

6. **Flagged but correct.** A row with the right name and timing is correct even if
   the app flagged it. The flag matters for the safety count, never for accuracy.

7. **Missed and extra.** A key row with no model row paired to it is dangerous
   (wrong and not flagged). A model row that is not in the key is wrong, flagged if
   the app flagged it, dangerous otherwise.

8. **Pairing threshold.** 60 (fuzz ratio on squashed names), greedy highest-first,
   each row used once.

9. **Dangerous-error target.** **0.** The app's core promise is that it never shows
   a confident wrong answer. Any dangerous error in the final run is a failure to
   report honestly, not a number to average away.

## Note on the test set

The answer key must be confirmed by someone who can read the handwriting. If it is
not, the accuracy numbers are wrong and nothing in the output will show it.