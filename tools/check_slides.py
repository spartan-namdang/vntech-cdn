#!/usr/bin/env python3
"""Check deck/index.html against the deck rules.

  - at most 55 slides, all on one horizontal line (no nested sections)
  - 6x6 rule: at most 6 lines of main text per slide, about 6 words per line.
    "About 6" is read as up to 8 words; lines of 7 or 8 words are counted
    and reported. A slide with 7 or 8 lines is an accepted overrun and listed.
  - every slide has speaker notes
  - every image slot has a DIAGRAM comment and an entry in images/README.md
  - no hard-coded colours in index.html

"Main text" is every <li> and <p> in the slide body. Titles, eyebrows,
tables, code blocks, diagrams, image-slot placeholders, chips, big figures
and speaker notes are not counted.

Usage:  python3 tools/check_slides.py          (run from the repo root)
Exit code is 1 when a hard rule is broken; 6x6 overruns are listed, not fatal.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "deck" / "index.html"
IMAGES_README = ROOT / "deck" / "images" / "README.md"

MAX_SLIDES = 55
MAX_LINES = 6    # the rule
SOFT_LINES = 8   # accepted overrun, listed in the report
MAX_WORDS = 6    # the target
SOFT_WORDS = 8   # "about 6": anything longer fails

SKIP_TAGS = {"table", "pre", "svg", "aside", "header", "figure", "footer"}
SKIP_CLASSES = {"eyebrow", "chips", "chip", "stat", "stat-row", "qr-row", "cover-meta", "card-kicker"}
LINE_TAGS = {"li", "p"}
VOID = {"img", "br", "hr", "meta", "link", "input", "use", "path", "rect", "circle"}


class Deck(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.slides = []
        self.stack = []          # (tag, skipping, is_line)
        self.cur = None
        self.depth_section = 0
        self.nested = 0
        self.line = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        if tag == "section":
            self.depth_section += 1
            if self.depth_section > 1:
                self.nested += 1
            self.cur = {"lines": [], "notes": False, "eyebrow": "", "title": "", "layout": ""}
            self.cur["layout"] = " ".join(sorted(c for c in classes if c.startswith("l-")))
            self.slides.append(self.cur)
        if self.cur is None or tag in VOID:
            return
        parent_skip = self.stack[-1][1] if self.stack else False
        skip = parent_skip or tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)
        if tag == "aside" and "notes" in classes:
            self.cur["notes"] = True
        is_line = (not skip) and tag in LINE_TAGS and self.line is None
        if is_line:
            self.line = []
        capture = None
        if tag == "p" and "eyebrow" in classes:
            capture = "eyebrow"
        elif tag in ("h1", "h2"):
            capture = "title"
        self.stack.append((tag, skip, is_line, capture))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "section":
            self.depth_section -= 1
            self.cur = None
            self.stack = []
            self.line = None
            return
        while self.stack:
            t, _skip, is_line, _cap = self.stack.pop()
            if is_line and self.line is not None:
                text = " ".join("".join(self.line).split())
                if text:
                    self.cur["lines"].append(text)
                self.line = None
            if t == tag:
                break

    def handle_data(self, data):
        if self.cur is None or not self.stack:
            return
        for _t, _s, _l, cap in reversed(self.stack):
            if cap:
                self.cur[cap] += data
                break
        if self.line is not None and not self.stack[-1][1]:
            self.line.append(data)


def words(text):
    return [w for w in re.split(r"\s+", text) if re.search(r"\w", w)]


def main():
    html = DECK.read_text(encoding="utf-8")
    deck = Deck()
    deck.feed(html)
    slides = deck.slides
    hard = []

    print(f"Slides: {len(slides)} (limit {MAX_SLIDES})")
    if len(slides) > MAX_SLIDES:
        hard.append(f"{len(slides)} slides, limit is {MAX_SLIDES}")
    if deck.nested:
        hard.append(f"{deck.nested} nested (vertical) section(s)")

    missing_notes = [i for i, s in enumerate(slides, 1) if not s["notes"]]
    if missing_notes:
        hard.append(f"slides without speaker notes: {missing_notes}")

    too_many, overrun, long_lines = [], [], []
    total_lines = lines_7_8 = 0
    print("\n  #  lines  max-words  slide")
    for i, s in enumerate(slides, 1):
        counts = [len(words(l)) for l in s["lines"]]
        n, mw = len(counts), max(counts, default=0)
        total_lines += n
        lines_7_8 += sum(1 for c in counts if MAX_WORDS < c <= SOFT_WORDS)
        label = " ".join((s["eyebrow"] or s["title"]).split())[:58]
        flag = ""
        if n > SOFT_LINES:
            flag = "  << too many lines"
            too_many.append(i)
        elif n > MAX_LINES:
            flag = "  < accepted overrun"
            overrun.append(i)
        if mw > SOFT_WORDS:
            flag += "  << line too long"
            long_lines.append(i)
        print(f"{i:3}  {n:5}  {mw:9}  {label}{flag}")

    print(f"\nMain-text lines: {total_lines}, of which {lines_7_8} have 7 or 8 words (none may have more)")
    print(f"Slides with 7 or 8 lines (accepted overrun): {overrun or 'none'}")
    for i in overrun + too_many + long_lines:
        s = slides[i - 1]
        print(f"\n  slide {i}: {' '.join(s['eyebrow'].split())}")
        for l in s["lines"]:
            print(f"    {len(words(l)):2}w  {l}")
    if too_many:
        hard.append(f"slides with more than {SOFT_LINES} lines: {too_many}")
    if long_lines:
        hard.append(f"slides with a line over {SOFT_WORDS} words: {long_lines}")

    # image slots: DIAGRAM comment directly above, and listed in images/README.md
    slots = re.findall(r'<img src="images/([^"]+)"', html)
    readme = IMAGES_README.read_text(encoding="utf-8") if IMAGES_README.exists() else ""
    print(f"\nImage slots: {len(slots)}")
    for name in slots:
        has_spec = re.search(r"<!-- DIAGRAM: " + re.escape(name) + r"\b.*?-->\s*<figure class=\"img-slot\">\s*<img src=\"images/" + re.escape(name), html, re.S)
        listed = name in readme
        exists = (ROOT / "deck" / "images" / name).exists()
        print(f"  {name:28} spec={'yes' if has_spec else 'NO'}  listed={'yes' if listed else 'NO'}  file={'present' if exists else 'not drawn yet'}")
        if not has_spec:
            hard.append(f"{name}: no DIAGRAM comment above the slot")
        if not listed:
            hard.append(f"{name}: not listed in deck/images/README.md")

    # hard-coded colours and inline font sizes in the slides
    body = html.split('<div class="reveal">', 1)[-1]
    colours = re.findall(r"#[0-9a-fA-F]{3,8}\b(?![^<]*</code>)|rgba?\(|hsla?\(", re.sub(r"<aside.*?</aside>|<pre.*?</pre>|<!--.*?-->", "", body, flags=re.S))
    inline = re.findall(r'style="[^"]*"', body)
    if colours:
        hard.append(f"hard-coded colours in slides: {sorted(set(colours))}")
    if inline:
        hard.append(f"inline styles in slides: {len(inline)}")
    print(f"\nHard-coded colours in slides: {len(colours)}   inline styles: {len(inline)}")

    if hard:
        print("\nFAILED:")
        for h in hard:
            print("  - " + h)
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
