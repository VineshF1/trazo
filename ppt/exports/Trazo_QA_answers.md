# Trazo — Q&A answer sheet (short answers; off-screen)

## The project

Trazo is a web page for the phone. You take a photo of a paper prescription, and it tells
you what medicines are written on it and how to take them.

The problem: doctors write fast, in short forms like BD and 1-0-1. Patients cannot read
it, so they may take a wrong dose or skip a medicine.

How it works: the photo is cleaned up, then a vision model reads it. The app then checks
every medicine name against its list of 91 Indian medicines, turns codes like 1-0-1 into
"morning, night", and shows a table. Every row gets a status word:

- **OK** — the name matched the list, the timing made sense.
- **Check this** — the app is not sure, please confirm with the pharmacist.
- **Unclear** — the handwriting could not be read. It never guesses a word.

The checking part is the real work of the project. The model can only read — the list
match, the timing rules and the flags make the reading safe to use. Every result also
says: a reading aid, not medical advice. No photo is ever stored.

The limits: the list is small, so unknown names are flagged; it does not check doses;
and it is not clinically validated — a learning project.

**The measured claim to say out loud:** the app never shows a confident wrong answer and
never drops a medicine — zero and zero across all 32 scored items. What it can't confirm,
it flags.

## "Why build this when ChatGPT can do all of this?"

Because ChatGPT gives an answer, Trazo can refuse to give one. Four checks decide every
row — anything unconfirmed is flagged Check this or Unclear. With medicines, a red
"I couldn't read this" beats a confident guess. The baseline-vs-pipeline test proves it.

## "But ChatGPT is free and works right now, what does Trazo add?"

Three things:
1. **Abstention** — it flags instead of guessing.
2. **Fixed rows** — name, strength, take-times, days, status. A patient or pharmacist can use it directly.
3. **Measurement** — the same steps run every time, so accuracy can be scored. A chat conversation can't be graded that way.

## "Would you type the prescription into ChatGPT instead of photographing it?"

Patients photograph; they don't retype — that's what the app is built for, no install, no login.
And the photo is processed in memory and deleted. Nothing stored, ever.

## "What is the innovation? It is one API call, where is the coding?"

The coding is everything around the call: resize and rotation fix, OpenCV cleanup, the strict
JSON prompt, RapidFuzz matching, the timing decoder, the four-check rule, SQLite corrections.
The model is a part I rent — my work makes it safe and testable.

## "Why not Google Lens? It reads handwriting too."

Lens copies text, it doesn't decode it. It can't turn "Tab Azo 500 1-0-1 x5" into a dose
schedule, match brands, or flag unsure words. It's a text reader; Trazo is a reading-with-verdict system.

## "What if the model is wrong — will a patient be harmed?"

Anything the rules can't confirm is flagged, and every result says "reading aid, not medical
advice — confirm with your pharmacist". The dangerous number — wrong but not flagged — is
exactly what the test run measures. Until then I claim nothing.

## Why not just use a chatbot?

A plain chatbot has no matching rules — it can never flag a row. That's what the baseline vs
pipeline comparison shows; the table comes after the first test run.

## Did you train a model?

No. A ready-made vision model is called through an API. The work is in the prompt, matching
rules, flags and testing.

## Is it ready for real patients?

No. Not clinically validated — a learning project. I say the limits before anyone asks.

## "Why does it need a medicine list to answer perfectly?"

The list is not the answer source — the model reads the handwriting. The list is the check: a read name that matches one of 91 known medicines gets a confident OK, and anything unknown is flagged Check this instead of guessed. A bigger list means more names it can confirm — that is future work.

## Other questions you may get

**How does a row earn OK?** Four checks: model didn't mark it unclear, database match is
strong (RapidFuzz), timing code known, no close second medicine name. Fail any → Check this or Unclear.

**Is my photo stored?** No. Processed in memory, deleted on response. Corrections store only
the text pair, never a photo.

**What if a medicine isn't in your list?** The row stays Check this — flagged, never dropped or filled in. If the name was searched online and no medicine exists under it, the flag says so: "No medicine with this name exists in the reference list — verify the spelling on the paper." The small list is exactly why this stays a learning project, not a production system.

**Can it still be wrong?** Yes — that's why we measure "wrong but not flagged" in the test run.
No numbers claimed before that.

**Is it an app?** A mobile web page: open in the phone browser, take a photo, get rows back.
No install, no login.

**Timing codes?** 1-0-1 = morning–no–night, BD = twice a day, SOS = as needed. The decoder
turns them into plain take-times.

**Why the "reading aid" banner?** So nobody mistakes a reading for medical advice. Confirmed
with the pharmacist — not by my project.

**What happens to a bad photo?** The app refuses it and asks for a retake — that refusal is
part of the demo, not a failure.
