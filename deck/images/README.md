# Images to draw

Each file below fills one image slot in the deck. Until the file exists, the slide shows a dashed frame with the file name. Drop a file with the exact name into this folder and it appears; no HTML edit is needed.

The full drawing spec for each image is the `<!-- DIAGRAM: ... -->` comment directly above its slot in `../index.html`.

| File | Slide | What to draw |
|---|---|---|
| `cdn-overview.svg` | 3 · 1.2 What a CDN is | Map with one origin and many edges; users in Hanoi and Paris each reach a nearby edge, and edges call the origin only on a MISS. |
| `request-lifecycle.svg` | 8 · 2.2 Request lifecycle | Sequence diagram: DNS, connect, cache lookup, then the short HIT path next to the longer MISS path. |
| `tiered-caching.svg` | 11 · 2.5 Tiered caching and origin shield | Two panels: every PoP calling the origin, versus PoPs calling a small upper tier that calls the origin once. |
| `isp-embedded-cache.svg` | 12 · 2.6 ISP peering and embedded caches | Three lanes to a subscriber: via transit, via peering at an IXP, and from a cache inside the ISP. |
| `cache-stampede.svg` | 21 · 3.8 Cache stampede | Two panels: thousands of misses hitting the origin, versus one collapsed request answering everyone. |
| `connection-pool.svg` | 31 · 5.2 Persistent connections to the origin | Many short user connections into the edge, a few warm ones to the origin, plus the keep-alive timeout pitfall. |
| `cloudfront-hooks.svg` | 38 · 7.1 CloudFront hook points | Viewer, edge cache and origin with the four hook points numbered on the arrows. |

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
