# Images to draw

Each file below fills one image slot in the deck. Until the file exists, the slide shows a dashed frame with the file name. Drop a file with the exact name into this folder and it appears; no HTML edit is needed.

The full drawing spec for each image is the `<!-- DIAGRAM: ... -->` comment directly above its slot in `../index.html`.

| File | Slide | What to draw |
|---|---|---|
| *(none at the moment)* | | Every diagram is currently an inline animated SVG in `../index.html`. |

## Format

- SVG, about 1200 × 900 px or larger (the slot is roughly 4:3). The image is scaled to fit and never cropped.
- The slot keeps a white background in both the light and the dark theme, so draw for a light background and one file works for both.
- To use another format, change the extension in the `src` of that slot in `index.html` (and in this table).

## Colours used elsewhere in the deck

Matching these keeps your drawings consistent with the inline diagrams:

| Meaning | Colour |
|---|---|
| Request, user | blue `#1746c9` |
| Edge, PoP | teal `#0b6f7c` |
| Cache HIT, fast path | green `#12733b` |
| Cache MISS, slow path | amber `#9a5200` |
| Origin | purple `#6d35b5` |
| Error (only) | red `#c0211f` |
