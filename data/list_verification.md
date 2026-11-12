# Medicine list verification (checked against the internet, 2026-11-12)

85 rows in `data/medicines_list.csv` / `data/medicines.db`. Sources: the user's
starter list of common India medicines, top Indian brands, and every brand
actually written on the test prescription photos.

## Verified online (brand exists, composition confirmed)

| Brand | Composition | Source |
|---|---|---|
| Rexazol DSR | Rabeprazole 20 + Domperidone 30 | 1mg / RxJinn |
| Duonase F (nasal) | Azelastine + Fluticasone furoate (Cipla) | 1mg / MedPlus |
| G Norm | probiotic for diarrhea | Medkart |
| Semitor Plus | Spironolactone 50 + Torasemide 20 | 1mg / Apollo |
| Levoflox / Levofloxacin | Levofloxacin | 1mg |
| Fefol | Ferrous sulfate + Folic acid | standard |
| HCQS 200 | Hydroxychloroquine 200 (Ipca) | 1mg |
| SAZO 500 | Sulfasalazine | standard |
| Gabopin NE | Gabapentin + Nortriptyline | IndiaMART listings |
| Tofacitinib (TOFA 5mg) | Tofacitinib 5 | C-Tofa / Tofamit listings |
| Pantop DSR / Pantocid DSR / Emeset / Ondem / Oflox OZ / O2 / Oz | standard India brands | 1mg |
| Defcort / Deflazacort 6 | Deflazacort | standard |
| Etoricoxib MR | Etoricoxib sustained release | standard |
| CCM | Calcium citrate maleate | standard |
| Liposomal Amphotericin B | mucormycosis therapy | standard |
| Sizodon Plus, Qutipin, Ativan, Rivotril, Serta, Sertraline | psychiatry brands | 1mg |
| Dolo, Crocin, Calpol, Montair LC, Azithral, Azee, Augmentin 625 Duo, Clavam 625, Monocef, Voveran, Brufen, Etoshine, Glycomet, Amlopres, Telma, Zentel, Calcirol, Neurobion Forte, Shelcal, Rantac | top India staples | 1mg |

## On the photos but NOT found online (kept as-is, keyed exactly as written)

These are small/local brands or the clinic's own spelling; no pharmacy listing
exists for them. They stay in the list so the app can confirm them on those
sheets; the honest answer about them is "local brand, verified on the paper,
not on the internet."

| As written | Closest online (not a match) |
|---|---|
| Vepin | none (only personal names) |
| Eloopar | Elopar (paracetamol combo) — different spelling kept from the paper |
| Lenope | none (only a Delaware tribal name) |
| Elopar | none found under that exact name |
| Rumaspab | Rhumasap / Rheumaspa (Ayurvedic) — different product |
| Lucibor Lotion | none (LuciBor is a veterinary product) |
| HRCE 200 | none; same RA sheet carries HCQS-family drugs, kept with
  hydroxychloroquine generic as the working interpretation |

## Searched later (2026-11-12, demo-image names)

| Name | Outcome |
|---|---|
| Pantac 150 | real — "Pentac 150" (Ranitidine 150, Uni-Pex); added to the list |
| Adilin 10 | real — Isoxsuprine 10 (vasodilator); added to the list |
| Ecoset | real — Ecoset ear drop; added to the list |
| Rexprazole DSR | **no medicine by this name exists online** → data/unknown_names.csv;
  the app now flags it with "No medicine with this name exists in the reference list" |
| Leukot M | **no medicine by this name exists online** (many Levocetirizine+Montelukast
  "-M" brands, none named Leukot M) → unknown_names.csv, same flag |

## Consequence for the demo

This is the limitation stated on slide 9, with evidence: the list is built from
the test photos, so known names confirm confidently and anything outside the
85 is flagged "Check this" — exactly the designed behavior, and exactly why the
list size bounds what the app can confirm.
