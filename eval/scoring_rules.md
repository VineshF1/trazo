# Scoring rules

**Status: open questions, not decided. Fill this in before running the harness on
Group B.** If this file is silent on a question, the rule in
`eval/scoring.py` applies, and that rule is a placeholder.

The harness runs with the rules as written here. Any answer you write here should
also be applied in `eval/scoring.py`, in these functions:

| Question | Where it lives | Current placeholder |
|---|---|---|
| Is "Dolo 650" the same as "Paracetamol 650 mg"? | `names_equal()` | No. Brand and generic are different strings, so this counts as wrong. |
| Does a missing strength count as wrong? | `_score_pair()`, `fields` | Strength is not scored at all yet. |
| Does a flagged row with the right name count as correct? | `_score_pair()` | Yes. A correct name is correct whether or not the row is flagged. A flag never turns a right answer into a wrong one. |
| Which fields decide "correct"? | `_score_pair()`, `fields` | Name and timing. Strength and duration are not scored. |
| Are "1-0-1" and "1 - 0 - 1" the same timing? | `normalize_timing()` | Only after stripping whitespace and uppercasing. So no: the spaces stay in the middle. |
| What pairing threshold is used? | `config.PAIRING_THRESHOLD` | 60 (starting guess). |
| What is the maximum acceptable number of dangerous errors? | no target set | **Not set.** Set a target here before the final run, so the target cannot be bent to fit the result. |

## Decisions to make

Write your answer after each question. Leave a question blank to keep the
placeholder.

1. **Brand vs generic.** Is a generic name an acceptable answer when the key has the
   brand, or the other way round?

2. **Strength.** Should a wrong or missing strength make an item wrong? If yes, what
   counts as the same strength: "650 mg", "650mg", "650"?

3. **Duration.** Should duration count toward an item being correct?

4. **Flagged but correct.** Confirm the placeholder: a right name that carries a
   "Check this" flag still counts as correct. (The flag matters for the safety
   count, not for accuracy.)

5. **Dangerous-error target.** The most important number in the report. State the
   number you will accept before you see the result.

6. **Timing normalization.** Should "1-0-1" and "1 - 0 - 1" be treated as the same?
   Should "BD" and "B.D." be treated as the same?

7. **Missed and extra.** Confirm the placeholder: a key row with no model row counts
   as wrong and not flagged (dangerous), and a model row that is not in the key
   counts as wrong.

## Note on the test set

The answer key must be confirmed by someone who can read the handwriting. If it is
not, the accuracy numbers are wrong and nothing in the output will show it.