# Trazo — Speaker Notes

## 01_title

Good morning. This is Trazo — a mini project about reading prescriptions. The one-line promise is on the slide: it is honest about what it cannot read, and the accuracy plan is built to measure that. The name means pen stroke in Spanish — the word beneath is where the reading starts.

## 02_problem

Here is a prescription photo — an anonymized real prescription from a public collection, patient details removed. I point at the slide: this is a real prescription. Doctor handwriting and short dose forms defeat plain reading, and a wrong dose or a skipped medicine is a real risk. That risk is the reason the project exists.

## 03_gap

Left side: who this is for. Patients and family members, and caregivers managing medicines for elderly parents — people holding a phone. Not for doctors or pharmacists. The gap is on the right: most tools show confident output even when the reading is wrong. Trazo does the opposite — it shows what it could not read.

## 04_what

This is the real result screen from the running app. Three things happen: it reads a prescription photo, it shows medicine, strength, timing and duration, and it marks every unclear word instead of guessing. The banner text on the slide is exactly what the app shows on every result — reading aid, not medical advice, confirm with your pharmacist.

## 05_how

Six steps, left to right, one per click, each with its job printed inside: photo from the camera, clean and resize to fix tilt and size, the vision model reads the words, match against the medicine list, decode timing codes like 1-0-1 and BD, and the result screen shows each row with its flag — OK, Check this, or Unclear. The photo itself is processed in memory and deleted — it is never stored.

## 06_stack

The stack is deliberately plain — a table is meant to be read, so this slide has no animation. Browser, Python and FastAPI on the server, OpenCV and Pillow for image handling, RapidFuzz for name matching, SQLite for storage, and a ready-made vision model called through an API. Free model API, no training — the accuracy work is in the rules, not the model.

## 07_safety

Five design decisions, one per click. It never fills an unreadable word — it flags it instead. Then the rule: anything the rules cannot confirm becomes Check this or Unclear — that is the amber tag. Whether a row earns the green OK is decided by four checks: the model did not mark it unclear, the database match is strong, the timing code is known, and no second medicine name is a close match. The warning on every result, no photo is stored, and no dose advice or diagnosis. The boundaries get their own slide at the end of the talk.

## 08_demo

Now the demo, on a phone, using the camera. The three real screens: home, result, and a caught failure — the blank photo the app refused, with the hatched could-not-read block marked on it. I will run the live demo after this slide. The refusal screen is part of the demo, not an exception to it.

## 09_limits

I will say the limits before anyone asks. The medicine list covers only the number shown — a name on the list is matched accurately, and a name off it stays Check this. That small list is the real limit: this is not a production system yet. It also reads what is written — it does not check doses. And no clinical validation: a learning project.

## 10_next

The summary is the whole project in three lines: it reads a prescription photo and lists each medicine, it flags every word it cannot read because it never guesses, and it warns on every result that this is a reading aid, not medical advice. That closes the talk — I end on thank you and invite questions out loud rather than on the slide. The small link at the bottom is the GitHub repo, for anyone who wants to look at the code after.
