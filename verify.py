#!/usr/bin/env python3
"""verify.py -- checks for news-image-20261126 v2 (37 stories, 9 regions).

Checks the rendered entry.png AND the source data in main.py:
  size, title margins, story/region counts, headline completeness,
  brief one-line fit, DATE CHECK, timeline, trap numbers, Pillow rules,
  output-dir rules, README badges.
Exit 0 when all PASS, 1 otherwise.
"""
import importlib.util
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PASS = []
FAIL = []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print("%s  (%s) %s" % ("PASS " if ok else "FAIL ", name, detail))


def main():
    # ---- load main.py data (import only; render is under __main__ guard) ----
    spec = importlib.util.spec_from_file_location("entry_main",
                                                  os.path.join(HERE, "main.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    src = open(os.path.join(HERE, "main.py"), encoding="utf-8").read()

    # ---- image ----
    try:
        from PIL import Image, ImageDraw
    except Exception:
        print("FAIL  (img) PIL unavailable")
        return 1
    img_path = os.path.join(HERE, "entry.png")
    im = Image.open(img_path).convert("RGB")
    check("a", im.size == (1024, 1024), "size %s" % (im.size,))

    # title margins: dark pixels in title band y=10..64
    def is_dark(px):
        r, g, b = px
        return r < 90 and g < 90 and b < 90
    xs = [x for y in range(10, 64) for x in range(1024)
          if is_dark(im.getpixel((x, y)))]
    if xs:
        lm, rm = min(xs), 1023 - max(xs)
        check("b", lm >= 20 and rm >= 20,
              "title margins left %dpx, right %dpx" % (lm, rm))
    else:
        check("b", False, "no title pixels found")

    # ---- story counts ----
    total = len(m.LEADS) + len(m.MEDIUM) + len(m.BRIEFS)
    check("c", total == 37, "total stories %d" % total)
    counts = m.region_counts()
    expect = {"Asia-Pacific": 9, "Americas": 5, "Europe": 10, "Africa": 5,
              "Oceania": 2, "Middle East": 4, "World": 2}
    check("c2", counts == expect, "regions %s" % (counts,))
    check("c3", len(m.LEADS) == 3 and len(m.MEDIUM) == 10,
          "3 big leads + 10 medium pictorials")
    check("c4", len(m.BRIEFS) == 24, "24 briefs (14-37)")

    # ---- every story has source + status ----
    # tuple shapes differ: LEADS/MEDIUM end (..., source, status, art),
    # BRIEFS end (..., source, status). Status is index -2 for pictorials.
    def _src_status(s, pictorial):
        if pictorial:
            return s[-3], s[-2]
        return s[-2], s[-1]
    bad = []
    for s in m.LEADS + m.MEDIUM:
        src_, st_ = _src_status(s, True)
        if not src_ or not st_:
            bad.append(s[0])
    for s in m.BRIEFS:
        src_, st_ = _src_status(s, False)
        if not src_ or not st_:
            bad.append(s[0])
    check("d", not bad, "stories missing source/status: %s" % bad)
    bad_status = []
    for s in m.LEADS + m.MEDIUM:
        if _src_status(s, True)[1] not in m.STATUS_COLORS:
            bad_status.append(s[0])
    for s in m.BRIEFS:
        if _src_status(s, False)[1] not in m.STATUS_COLORS:
            bad_status.append(s[0])
    check("d2", not bad_status, "unknown status: %s" % bad_status)

    # ---- headlines complete (no truncation marker, fits its card) ----
    d = ImageDraw.Draw(Image.new("RGB", (1024, 1024)))
    lead_w = (976 - 2 * 11) // 3
    med_w = (976 - 4 * 9) // 5
    bad_h = []
    for lead in m.LEADS:
        lines = m.wrap(d, lead[3], m._playfair(23), lead_w)
        if len(lines) > 3 or "..." in lead[3]:
            bad_h.append(lead[0])
    for med in m.MEDIUM:
        lines = m.wrap(d, med[2], m._serif(16, bold=True), med_w)
        if len(lines) > 3 or "..." in med[2]:
            bad_h.append(med[0])
    check("e", not bad_h, "headlines over 3 lines / truncated: %s" % bad_h)

    # ---- briefs fit one line (10px, column 326px) ----
    f_b = m._serif(10)
    over = []
    for b in m.BRIEFS:
        txt = "%d. %s — %s — %s" % (b[0], b[2], b[3], b[4])
        if b[5] == "FORECAST":
            txt += " · FORECAST"
        if d.textlength(txt, font=f_b) > 326:
            over.append(b[0])
    check("e2", not over, "briefs over one line: %s" % over)

    # ---- summaries fit 2 lines (leads only; medium cards render no summary) ----
    bad_s = []
    for lead in m.LEADS:
        if len(m.wrap(d, lead[4], m._serif(12), lead_w)) > 2:
            bad_s.append(lead[0])
    check("e3", not bad_s, "lead summaries over 2 lines: %s" % bad_s)

    # ---- DATE CHECK + timeline + stats ----
    check("f", len(m.DATE_CHECK) == 12, "DATE CHECK items %d" % len(m.DATE_CHECK))
    check("f2", len(m.TIMELINE) == 6, "timeline entries %d" % len(m.TIMELINE))
    check("f3", len(m.STATS) == 6, "stat strip numbers %d" % len(m.STATS))

    # ---- trap numbers must NOT appear as Thursday facts ----
    all_text = " ".join(
        [s[3] for s in m.LEADS] + [s[4] for s in m.LEADS] +
        [s[2] for s in m.MEDIUM] + [s[3] for s in m.MEDIUM] +
        [s[3] for s in m.BRIEFS] + [n for n, _ in m.STATS])
    traps = []
    if "$3,645" in all_text:
        traps.append("gold $3,645 as Thursday")
    if "-6,2%" in all_text or "-6.2%" in all_text:
        traps.append("Kospi -6.2% as Thursday")
    if "180+" in all_text or "180 tewas" in all_text:
        traps.append("Cairo 180+ deaths")
    if "113–99" in all_text or "113-99" in all_text:
        traps.append("Celtics 113-99")
    check("g", not traps, "trap numbers present: %s" % traps)
    # correct Thursday numbers ARE present
    good = []
    if "$3,593" in all_text:
        good.append("COMEX $3,593")
    if "+0.86%" in all_text:
        good.append("Nikkei +0.86%")
    if "+0.29%" in all_text:
        good.append("Kospi +0.29%")
    if "3.25%" in all_text:
        good.append("BOK 3.25%")
    check("g2", len(good) == 4, "Thursday numbers present: %s" % good)

    # ---- no future-dated stories (no Friday 27 Nov / Saturday results) ----
    future = []
    for s in m.LEADS + m.MEDIUM + m.BRIEFS:
        txt = " ".join(str(x) for x in s)
        if "Friday 27" in txt or "27 Nov" in txt and "reported" in txt.lower():
            future.append(s[0])
    check("h", not future, "future-dated stories: %s" % future)

    # ---- source hygiene ----
    check("i", "..." not in src, "no '...' in main.py")
    # no top-level Pillow import: 'from PIL' / 'import PIL' must be inside try
    lines = src.split("\n")
    toplevel_pil = [ln for ln in lines
                    if (ln.startswith("from PIL") or ln.startswith("import PIL"))]
    check("i2", not toplevel_pil, "top-level Pillow import: %s" % toplevel_pil)
    check("i3", "MAKEFUN_OUTPUT_DIR" in src, "honours $MAKEFUN_OUTPUT_DIR")
    check("i4", "ENTRY_OUTPUT" in src, "honours $ENTRY_OUTPUT")
    check("i5", "/output/entry.png" in src, "falls back to /output/entry.png")
    check("i6", "shutil.copyfile" in src and "entry.png" in src,
          "fallback copies committed entry.png")

    # ---- README badges ----
    readme = open(os.path.join(HERE, "README.md"), encoding="utf-8").read()
    slug = "news-image-20261126"
    owner, repo = "mekzibnn", "news-world-today-26"
    badges = [
        "https://make.fun/badge/%s.svg" % slug,
        "https://make.fun/badge/%s/%s/%s/rank.svg" % (slug, owner, repo),
        "https://make.fun/badge/%s/%s/%s/reward.svg" % (slug, owner, repo),
    ]
    bad_b = [b for b in badges if b not in readme]
    check("j", not bad_b, "badges missing: %s" % bad_b)
    check("j2", "shields.io" not in readme, "no shields.io")
    check("j3", ("https://make.fun/bounty/%s" % slug) in readme,
          "badge links to bounty")

    # ---- LICENSE present ----
    check("k", os.path.exists(os.path.join(HERE, "LICENSE")),
          "MIT LICENSE present")

    # ---- pictorial layers stay inside their bands (no orange in timeline) ----
    def is_orange(px):
        r, g, b = px
        return r > 180 and 60 < g < 150 and b < 80
    # timeline band: find its y by scanning for the red "THE DAY IN UTC" text
    # (approximate: timeline is between map and DATE CHECK, y ~ 880-910)
    orange = 0
    for y in range(880, 912):
        for x in range(1024):
            if is_orange(im.getpixel((x, y))):
                orange += 1
    check("l", orange == 0, "flame-orange pixels in timeline band: %d" % orange)

    print("\n%d PASS, %d FAIL" % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
