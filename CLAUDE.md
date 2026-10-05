# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Reveal.js slide deck for a VNTech tech-sharing session on CDNs. Static site: no build step, no package manager, no dependencies to install. Everything is vendored and loaded by relative path so the deck works offline and under the GitHub Pages sub-path `/vntech-cdn/`. Do not add CDN links or absolute paths.

## Commands

```bash
python3 -m http.server 8001 --directory deck   # serve; opening index.html from disk breaks the speaker view
python3 tools/check_slides.py                  # run after every edit to deck/index.html (from the repo root)
```

`check_slides.py` is the only lint/test. It exits 1 on a hard-rule break; 6×6 overruns are only listed. Hard rules:

- at most 55 slides, all top-level (no nested `<section>`)
- every slide has `<aside class="notes">`
- no line of main text over 8 words; no slide over 8 lines (target is 6 lines × 6 words)
- every `.img-slot` has a `<!-- DIAGRAM: file.svg ... -->` comment above it and a row in `deck/images/README.md`
- no hard-coded colours and no `style="..."` in `index.html`

"Main text" is `<li>` and `<p>` in the slide body. Titles, eyebrows, tables, `<pre>`, SVG, figures, notes, and the classes in `SKIP_CLASSES` (chips, stats, card kickers, …) are not counted, so moving text into those is how a dense slide legitimately passes.

Deploy is automatic: a push to `main` touching `deck/**` publishes the `deck/` folder to GitHub Pages via `.github/workflows/deploy-pages.yml`.

## Architecture

Three hand-written files; `deck/vendor/` (reveal.js 6.0.2, qrcode-generator 2.0.4) is third-party and not edited.

- **`deck/index.html`** — every slide, in one flat sequence of `<section>` elements. Sections of the talk are separated by banner comments (`<!-- ==== ... -->`) and each slide begins with a number comment like `<!-- 3.4 -->`. An SVG icon sprite sits at the top; icons are used as `<svg class="icon"><use href="#i-name"/></svg>`.
- **`deck/css/deck.css`** — design tokens at the top (`:root` for light, `[data-theme="dark"]` override), then one block per layout class. All colours, font sizes, spacing and radii in slides must come from these tokens; inline SVG diagrams are coloured with the `.dg` classes.
- **`deck/js/deck.js`** — loaded in `<head>` so the saved theme applies before first paint; `Deck.init()` is called at the end of `index.html` after the vendor scripts. It does things the HTML relies on implicitly:
  - builds each slide's footer from its `data-section` attribute (do not write footers by hand)
  - runs the animated diagrams (`svg.dg-anim`) on the current slide, see below
  - toggles `.is-loaded` on `.img-slot` when its `<img>` actually loads, so dropping a correctly named file into `deck/images/` replaces the dashed placeholder with no HTML change
  - renders the Kahoot QR on canvas from `data-kahoot-url` / `data-kahoot-pin` on the `l-qr` section; empty attributes show a placeholder
  - theme toggle on `T`, persisted in `localStorage` (`cdn-deck-theme`) and synced to the speaker window through the `storage` event
  - Reveal config: fixed 1280×720 canvas, `center: false`, `hash: true`

## Slide conventions

Every slide uses the same frame: `<section class="l-…" data-section="N · Section name">` containing `header.s-head` (with `p.eyebrow` "3.4 · Topic" and an `h2` that states the takeaway), `div.s-body`, and `aside.notes`. To add a slide, copy an existing one with the layout you need.

Layout classes (one per slide): `l-cover`, `l-statement`, `l-bullets` (`ul.points` / `ol.steps`), `l-two-col` (`.cols > .col`, optional `.callout`), `l-figure` (+ `is-stacked`), `l-table` (`table.tbl`), `l-code` (+ `is-full`), `l-cards` (`.cards.c3|c4|c5`), `l-qr`.

- Slide text is in English; speaker notes are in Vietnamese.
- Use `class="fragment"` only where the slide tells a sequence.
- Slide numbers appear in several places: the `<!-- N.M -->` comment, the eyebrow, cross-references in other slides' text (e.g. "Multi-CDN (8.6)"), and the Slide column of `deck/images/README.md`. Inserting, removing or reordering slides means updating all of them.

## Animated diagrams

Most diagrams are inline `<svg class="dg dg-anim">` in a `figure.fig`, drawn with the `.dg` classes (so they follow the theme) and animated by the timeline in `deck.js`. Everything is declared in the markup, with times in seconds inside a loop:

- `data-loop="8"` on the `<svg>` (or on a scene group) is the loop length; it restarts when the slide or scene changes.
- `<circle class="pkt" data-along="#path-id" data-at="0.3, 5" data-dur="0.6">` is a dot that travels that path at those times; add `data-rev` to travel backwards. `.rail` is an invisible path used only for motion.
- `data-show="1 4, 5.7 7.4"` makes an element visible only in those windows (badges, lit markers, error states).
- `<g data-scene="name" data-loop="5">` groups are alternative states of one diagram. The first is the default; the last visible `.fragment[data-scene]` on the slide (a bullet, or the group itself) switches to it, so the clicker steps through them.

Path ids are document-wide, so prefix them per diagram (`rl-`, `tc-`, `isp-`, `st-`, `cp-`, `hk-`). Keep labels to a word or two; the presenter explains the rest.

## Image slots

Diagrams kept as image files (currently only `cdn-overview.svg` on 1.2) are `<figure class="img-slot">` blocks. The drawing spec is the `<!-- DIAGRAM: ... -->` comment directly above the slot, and `deck/images/README.md` is the index (file name, slide, description, format and colour guidance). The slot background stays white in both themes, so images are drawn for a light background. Adding a slot means: copy an existing figure block with its `DIAGRAM` comment, change the file name, add a row to `deck/images/README.md`.

`demo/` is reserved for the live demo and is currently empty.
