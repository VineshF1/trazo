<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: en
- audience: Lecturers and classmates. Plain talk, no invented numbers, presenter is a student.
- objective: They can state what Trazo does, that it flags what it cannot read, that measurement is designed but not yet run, and they know the safety boundary.
- core_message: A prescription reader that is honest about what it cannot read, with measured accuracy to prove it.
- consumption_mode: balanced

## mode
- mode: narrative
- mode_behavior: Open on the problem, show the product and its honesty machinery, close on limits and next steps before questions.

## visual_style
- visual_style: editorial
- visual_style_behavior: Printed pharmacy slip. Off-white paper, near-black ink, thin rules, 4 px corners, one blue accent, status colors only on status words with the word always written. Left-aligned, no shadows, no gradients.

## colors
- background: #FAF9F5
- panel: #F3F1EA
- primary: #171715
- accent: #1D4ED8
- positive: #1E6B3A
- warning: #7A5200
- negative: #B3261E
- body_text: #171715
- secondary_text: #4A4843
- divider: #D9D6CF

## typography
- font_family: Arial, sans-serif
- title_family: Arial, sans-serif
- body_family: Arial, sans-serif
- label_family: Arial, sans-serif
- display: 120
- title: 48
- subtitle: 32
- body: 27
- tag: 18
- brand: 28

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: tabler-outline/camera, tabler-outline/eye-off

## page_rhythm
- P01: breathing
- P02: breathing
- P03: anchor
- P04: anchor
- P05: dense
- P06: dense
- P07: anchor
- P08: dense
- P09: anchor
- P10: breathing

## pptx_structure
- mode: flat

## images
- p02_rxblur: images/rx-blur.png | source=user | crop=no-crop
- p04_result: images/app-result.png | source=user | crop=no-crop
- p08_home: images/app-home.png | source=user | crop=no-crop
- p08_retake: images/app-retake.png | source=user | crop=no-crop

## page_visualizations
- P06: table/stack_table

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
