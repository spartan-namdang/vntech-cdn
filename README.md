# vntech-cdn

Slide deck for the VNTech tech-sharing session on CDNs, by Nam Dang and Tuan Phan. Built with Reveal.js, presented from a browser, deployed to GitHub Pages.

```
vntech-cdn/
├── README.md
├── .github/workflows/deploy-pages.yml   deploys deck/ to GitHub Pages
├── tools/check_slides.py                slide count, 6×6 rule, notes, image slots
├── demo/                                reserved for the demo
└── deck/
    ├── index.html                       all slides, one section after another
    ├── css/deck.css                     colour tokens, type scale, layouts
    ├── js/deck.js                       theme switch, footers, image slots, QR, Reveal config
    ├── fonts/                           IBM Plex Sans and Mono (woff2)
    ├── images/                          diagrams to draw, see images/README.md
    └── vendor/                          reveal.js 6.0.2, qrcode-generator 2.0.4
```

## Run it

The deck has no build step. Serve the `deck/` folder over HTTP (opening `index.html` from disk breaks the speaker view):

```bash
python3 -m http.server 8001 --directory deck
```

Then open <http://localhost:8001>. Nothing is loaded from the Internet, so it works offline.

## Shortcuts

| Key | Action |
|---|---|
| `→` `Space` / `←` | Next / previous slide or step |
| `S` | Speaker view: notes (in Vietnamese), timer, next slide |
| `T` | Switch between the light and the dark theme. The choice is remembered. |
| `F` | Full screen |
| `O` | Overview of all slides |
| `G` | Jump to a slide number |
| `B` | Black out the screen |

The URL keeps the current slide (`#/12`), so a reload returns to the same place.

## Edit the deck

Everything is in `deck/index.html`. Sections are separated by banner comments, and each slide starts with a comment such as `<!-- 3.4 -->`.

### Add a slide

Copy a slide that uses the layout you need and change its content. A slide always has the same frame:

```html
<section class="l-bullets" data-section="3 · Caching">
  <header class="s-head">
    <p class="eyebrow">3.4 · Topic name</p>
    <h2>The conclusion the audience should take away</h2>
  </header>
  <div class="s-body">
    <ul class="points">
      <li>At most six lines</li>
      <li>About six words each</li>
    </ul>
  </div>
  <aside class="notes">
    <p>Speaker notes.</p>
  </aside>
</section>
```

`data-section` becomes the footer. Pick one layout class from the catalog:

| Class | Use for |
|---|---|
| `l-cover` | Cover |
| `l-statement` | A few big lines |
| `l-bullets` | A list (`ul.points`) or numbered steps (`ol.steps`) |
| `l-two-col` | Two columns (`.cols` > `.col`), with an optional `.callout` below |
| `l-figure` | A diagram or image slot beside the key points; add `is-stacked` to put the figure on top |
| `l-table` | A table (`table.tbl`) with optional captions |
| `l-code` | Code beside points; add `is-full` for a full-width code block |
| `l-cards` | A row of cards (`.cards.c3`, `.c4`, `.c5`) |
| `l-qr` | The Kahoot slide |

Rules that keep the deck consistent:

- Colours, font sizes, spacing and radii come from the tokens at the top of `css/deck.css`. Do not put `style="..."` or colour values in a slide. Inside SVG, use the `.dg` classes.
- Icons come from the sprite at the top of `index.html`: `<svg class="icon"><use href="#i-name"/></svg>`.
- To reveal content step by step, add `class="fragment"` to an element. Use it only where the slide tells a sequence.
- The deck is capped at 55 slides, on one horizontal line (no nested sections).

After editing, run the checks:

```bash
python3 tools/check_slides.py
```

### Add an image

Slots for the diagrams to draw are listed in `deck/images/README.md`. Save a file with the listed name into `deck/images/` and it replaces the dashed placeholder. The drawing spec for each one is the `<!-- DIAGRAM: ... -->` comment above its slot in `index.html`.

To add a new slot, copy an existing `<figure class="img-slot">` block together with its `DIAGRAM` comment, change the file name, and add a row to `deck/images/README.md`.

### Set the Kahoot link

Find the Kahoot slide near the end of `deck/index.html` and fill the two attributes on its `<section>`:

```html
<section class="l-qr" data-section="10 · Closing"
         data-kahoot-url="https://kahoot.it/?pin=1234567" data-kahoot-pin="1234567">
```

The QR code is generated in the browser from `data-kahoot-url` and is always black on white. While the attribute is empty, the slide shows a placeholder.

## Deploy to GitHub Pages

One-time setup:

1. Create a repository named `vntech-cdn` on GitHub.
2. From this folder: `git init -b main`, commit, add the remote, and push to `main`.
3. In the repository, open **Settings → Pages** and set **Source** to **GitHub Actions**.

After that, every push to `main` that touches `deck/**` (or the workflow file) deploys the `deck/` folder. The workflow can also be started by hand from the **Actions** tab (**Deploy deck to GitHub Pages → Run workflow**).

The deck is then at `https://<user>.github.io/vntech-cdn/`. All paths in the deck are relative, so it works under that sub-path.

## Credits

- [reveal.js](https://revealjs.com) 6.0.2, MIT
- [IBM Plex](https://github.com/IBM/plex) Sans and Mono, SIL Open Font License 1.1
- [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 2.0.4, MIT
