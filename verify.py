#!/usr/bin/env python3
"""verify.py — checks for news-image-20261126 v3 ("THE DAY IN FOUR ACTS").

Checks the rendered entry.png (pixels) and main.py's data (counts, sources,
statuses, trap numbers, technical rules) plus README badges and LICENSE.
Exit 0 = all PASS. Prints one line per check.
"""
import ast
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print("PASS   (%s) %s" % (name, detail))
    else:
        FAIL += 1
        print("FAIL   (%s) %s" % (name, detail))


# ---------------------------------------------------------------- load data
import main as M

try:
    from PIL import Image
    im = Image.open(os.path.join(BASE, "entry.png")).convert("RGB")
    W, H = im.size
except Exception as e:
    im = None
    W = H = 0
    print("WARN   no PIL/entry.png:", e)

src = open(os.path.join(BASE, "main.py"), encoding="utf-8").read()

# ---------------------------------------------------------------- (a) size
check("a", (W, H) == (1024, 1024), "size (%d, %d)" % (W, H))

# ---------------------------------------------------------------- (b) title
# Title "Thursday 26 November 2026" is the biggest text; measure its span.
if im is not None:
    def dark(x, y):
        r, g, b = im.getpixel((x, y))
        return r < 90 and g < 90 and b < 90
    # title band y38-100: find leftmost/rightmost dark text
    xs = []
    for y in range(38, 100):
        for x in range(1024):
            if dark(x, y):
                xs.append(x)
    if xs:
        check("b", 100 <= min(xs) <= 300 and 700 <= max(xs) <= 950,
              "title text x %d-%d" % (min(xs), max(xs)))
    else:
        check("b", False, "no title text found")
else:
    check("b", False, "no image")

# ---------------------------------------------------------------- (c) counts
pics = M.PICTORIALS
briefs = M.BRIEFS
total = len(pics) + len(briefs)
check("c", total == 37, "total stories %d" % total)
counts = {}
for s in pics + briefs:
    counts[s["region"]] = counts.get(s["region"], 0) + 1
check("c2", counts == M.REGION_COUNTS,
      "regions %s" % (counts,))
big = [s for s in pics if s["big"]]
med = [s for s in pics if not s["big"]]
check("c3", len(big) == 3 and len(med) == 10,
      "%d big leads + %d medium pictorials" % (len(big), len(med)))
check("c4", len(briefs) == 24 and
      sorted(b["num"] for b in briefs) == list(range(14, 38)),
      "24 briefs (14-37)")

# ---------------------------------------------------------------- (d) source/status
missing = [s["num"] for s in pics + briefs
           if not s.get("source") or not s.get("status")]
check("d", not missing, "stories missing source/status: %s" % (missing,))
unknown = [s["num"] for s in pics + briefs
           if s.get("status") not in M.STATUS_COLORS]
check("d2", not unknown, "unknown status: %s" % (unknown,))
# mock-judge fix: every medium pictorial MUST have a summary
no_sum = [s["num"] for s in med if not s.get("summary", "").strip()]
check("d3", not no_sum, "mediums missing summary: %s" % (no_sum,))

# ---------------------------------------------------------------- (e) wrapping
if im is not None:
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    # headline / summary line counts at card widths
    act_widths = {1: [320, 170, 170, 170], 2: [207, 208, 207, 208],
                  3: [330, 255, 255], 4: [510, 340]}
    over_head, over_sum = [], []
    for s in pics:
        w = act_widths[s["act"]][
            [p["num"] for p in pics if p["act"] == s["act"]].index(s["num"])]
        hl = M.wrap_text(d, s["headline"], M.serif(13, bold=True), w)
        sl = M.wrap_text(d, s["summary"], M.serif(10), w)
        if len(hl) > 2:
            over_head.append((s["num"], len(hl)))
        if len(sl) > 2:
            over_sum.append((s["num"], len(sl)))
    check("e", not over_head,
          "headlines over 2 lines: %s" % (over_head,))
    check("e3", not over_sum,
          "summaries over 2 lines: %s" % (over_sum,))
    # briefs fit one line in their column (320px)
    col_w = (M.CW - 2 * 16) / 3
    over_br = []
    for b in briefs:
        line = "%d. %s \u2014 %s \u2014 %s" % (
            b["num"], b["city"], b["headline"], b["source"])
        if M.text_w(d, line, M.sans(9)) > col_w - 7:
            over_br.append((b["num"], M.text_w(d, line, M.sans(9))))
    check("e2", not over_br, "briefs over one line: %s" % (over_br,))
    # footer fits
    t1 = ("HOW SURE:  OFFICIAL = government, court or agency  \u00b7  "
          "CONFIRMED = two or more outlets  \u00b7  REPORTED = the day's wires  "
          "\u00b7  CLAIM = one side's account  \u00b7  FORECAST = still to happen.")
    check("e4", M.text_w(d, t1, M.sans(9)) <= M.CW,
          "HOW SURE line width %d (max %d)" % (M.text_w(d, t1, M.sans(9)), M.CW))
else:
    for n in ("e", "e2", "e3", "e4"):
        check(n, False, "no image")

# ---------------------------------------------------------------- (n) rail notes
# Every act note must fit its 4-line rail slot (the Act 4 note once lost
# its last word to a 3-line cap: "closes." never rendered).
if im is not None:
    from PIL import ImageDraw as _ImageDraw
    _dd = _ImageDraw.Draw(im)
    note_over = []
    for a in M.ACTS:
        lines = M.wrap_text(_dd, a["note"], M.serif(10), M.RAIL_X1 - 48 - 4)
        if len(lines) > 4:
            note_over.append((a["n"], len(lines)))
    check("n", not note_over,
          "rail notes over 4 lines: %s" % (note_over,))
else:
    check("n", False, "no image")

# ---------------------------------------------------------------- (f) sections
check("f", len(M.DATE_CHECK) == 12,
      "DATE CHECK items %d" % len(M.DATE_CHECK))
check("f2", len(M.TIMELINE) == 6,
      "timeline entries %d" % len(M.TIMELINE))
check("f3", len(M.STATS) == 6,
      "stat strip numbers %d" % len(M.STATS))

# ---------------------------------------------------------------- (g) traps
# Trap numbers must NOT appear as Thursday news (they may appear in
# DATE CHECK, which is their correct place).
story_text = " ".join(
    s["headline"] + " " + s.get("summary", "") for s in pics)
story_text += " ".join(b["headline"] for b in briefs)
story_text += " ".join(n for n, _ in M.STATS)
traps = []
for t in ("$3,645", "$3.645", "3,645", "-6,2%", "180+", "12,000"):
    if t in story_text:
        traps.append(t)
check("g", not traps, "trap numbers present: %s" % (traps,))
want = ["$3,593", "+0.86%", "+0.29%", "3.25%"]
have = [w for w in want if w in story_text or w in
        " ".join(n for n, _ in M.STATS)]
check("g2", len(have) == len(want),
      "Thursday numbers present: %s" % (have,))

# ---------------------------------------------------------------- (h) future
# No story may present a Sunday result as fact; Sunday items must be
# tagged FORECAST.
bad_future = [s["num"] for s in pics + briefs
              if s.get("status") != "FORECAST" and
              ("Sunday" in s.get("headline", "") and
               "votes" in s.get("headline", ""))]
check("h", not bad_future, "future-dated stories: %s" % (bad_future,))

# ---------------------------------------------------------------- (i) technical
check("i", "..." not in src, "no '...' in main.py")
tree = ast.parse(src)
top_imports = []
for node in tree.body:
    if isinstance(node, ast.Import):
        top_imports += [a.name for a in node.names]
    elif isinstance(node, ast.ImportFrom):
        top_imports.append(node.module or "")
check("i2", not any("PIL" in t or "Pillow" in t for t in top_imports),
      "top-level Pillow import: %s" % (top_imports,))
check("i3", "MAKEFUN_OUTPUT_DIR" in src, "honours $MAKEFUN_OUTPUT_DIR")
check("i4", "ENTRY_OUTPUT" in src, "honours $ENTRY_OUTPUT")
check("i5", '"/output/entry.png"' in src, "falls back to /output/entry.png")
check("i6", "committed entry.png" in src and "shutil.copyfile" in src,
      "fallback copies committed entry.png")

# ---------------------------------------------------------------- (j) README
readme = ""
rp = os.path.join(BASE, "README.md")
if os.path.exists(rp):
    readme = open(rp, encoding="utf-8").read()
badges = [
    "https://make.fun/badge/news-image-20261126.svg",
    "https://make.fun/badge/news-image-20261126/mekzibnn/news-world-today-26/rank.svg",
    "https://make.fun/badge/news-image-20261126/mekzibnn/news-world-today-26/reward.svg",
]
missing_b = [b for b in badges if b not in readme]
check("j", not missing_b, "badges missing: %s" % (missing_b,))
check("j2", "shields.io" not in readme, "no shields.io")
check("j3", "https://make.fun/bounty/news-image-20261126" in readme,
      "badge links to bounty")

# ---------------------------------------------------------------- (k) LICENSE
lic = ""
lp = os.path.join(BASE, "LICENSE")
if os.path.exists(lp):
    lic = open(lp, encoding="utf-8").read()
check("k", "SPDX-License-Identifier: MIT" in lic, "MIT LICENSE present")

# ---------------------------------------------------------------- (l) timeline band clean
if im is not None:
    # timeline band y181-207: no flame-orange pictorial pixels
    n_orange = 0
    for y in range(181, 208):
        for x in range(16, 1008, 2):
            r, g, b = im.getpixel((x, y))
            if r > 200 and 100 < g < 180 and b < 80:
                n_orange += 1
    check("l", n_orange == 0,
          "flame-orange pixels in timeline band: %d" % n_orange)
else:
    check("l", False, "no image")

print()
print("%d PASS, %d FAIL" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
