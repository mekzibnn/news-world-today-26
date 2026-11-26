"""verify.py — automated checks for news-image-20261126 v1.

Checks (exit 0 = all PASS, exit 1 = any FAIL):
  (a) entry.png is 1024x1024
  (b) title margins: date-headline glyphs do not touch the edges (>=40px)
  (c) all 13 headlines + 15 briefs complete (no truncation, no '...')
  (d) font sizes: briefs >=18px, DATE CHECK >=16px, timeline >=16px
  (e) timeline times/zones match the research
  (f) region counts correct (7/5/10/0/0/4/2 = 28)
  (g) DATE CHECK has 41 items
  (h) pictorial bands have content + shading (>=3 brightness levels)
  (i) README has the 3 live make.fun badges, no shields.io
  (j) no '...' anywhere in main.py
  (k) main.py honours $MAKEFUN_OUTPUT_DIR + fallback, no top-level Pillow import
"""

import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PASS = []
FAIL = []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("PASS  " if ok else "FAIL  ") + f"({name})" +
          (f" {detail}" if detail else ""))


def load_main():
    spec = importlib.util.spec_from_file_location(
        "entry_main", os.path.join(HERE, "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    try:
        from PIL import Image
    except Exception:
        print("FAIL  (a) Pillow not available")
        return 1
    m = load_main()

    # (a) size
    try:
        im = Image.open(os.path.join(HERE, "entry.png"))
        check("a", im.size == (1024, 1024), f"size {im.size}")
    except Exception as e:
        check("a", False, f"cannot open entry.png: {e}")
        im = None

    # (b) title margins — dark glyph pixels in date-headline band y 38-72
    if im is not None:
        band = im.crop((0, 38, 1024, 72)).convert("L")
        px = band.load()
        minx, maxx = 1024, 0
        for y in range(band.height):
            for x in range(band.width):
                if px[x, y] < 80:
                    minx = min(minx, x)
                    maxx = max(maxx, x)
        left, right = minx, 1023 - maxx
        check("b", left >= 40 and right >= 40,
              f"title margins left {left}px, right {right}px")
        # masthead text margins
        band2 = im.crop((0, 0, 1024, 36)).convert("L")
        px2 = band2.load()
        minx2, maxx2 = 1024, 0
        for y in range(band2.height):
            for x in range(band2.width):
                if px2[x, y] > 180:
                    minx2 = min(minx2, x)
                    maxx2 = max(maxx2, x)
        check("b2", minx2 >= 10 and 1023 - maxx2 >= 10,
              f"masthead margins left {minx2}px, right {1023 - maxx2}px")

    # (c) 13 headlines + 15 briefs complete
    leads = getattr(m, "LEADS", [])
    mediums = getattr(m, "MEDIUMS", [])
    headlines = [h for (_, h, _, _, _, _) in leads] + \
                [h for (_, _, h, _, _, _) in mediums]
    check("c", len(headlines) == 13, f"headlines count {len(headlines)}")
    bad_h = [h for h in headlines if not h or "..." in h or h.strip() != h]
    check("c2", not bad_h, f"headlines complete bad={bad_h}")
    briefs = getattr(m, "BRIEFS", [])
    check("c3", len(briefs) == 15, f"briefs count {len(briefs)}")
    bad_b = [t for (t, _) in briefs if not t or "..." in t]
    check("c4", not bad_b, f"briefs complete bad={bad_b}")
    # briefs fit one line at 18px in the brief column (516px)
    try:
        from PIL import ImageDraw, ImageFont
        tmp = Image.new("RGB", (1024, 1024))
        dd = ImageDraw.Draw(tmp)
        f18 = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        f18b = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        over = []
        for i, (t, _) in enumerate(briefs, 1):
            wnum = dd.textlength(f"{i}. ", font=f18b)
            wt = dd.textlength(t, font=f18)
            if wnum + wt > 516:
                over.append((i, t))
        check("c5", not over, f"briefs fit one line over={over}")
    except Exception as e:
        check("c5", False, f"measure failed: {e}")

    # (d) font sizes from source
    with open(os.path.join(HERE, "main.py")) as f:
        src = f.read()
    check("d", "f_br = font(18)" in src, "briefs 18px")
    check("d2", "f_dc = font(16)" in src, "DATE CHECK 16px")
    check("d3", "f_tl = font(16)" in src, "timeline 16px")

    # (e) timeline times/zones
    tl = getattr(m, "TIMELINE", [])
    flat = [e for row in tl for e in row]
    expected_times = ["Wed ET", "00:45", "03:00", "08:00",
                      "14:00", "16:00", "16:30", "02:38 Fri"]
    got_times = []
    for e in flat:
        got_times.append(e.split(" · ")[0] if " · " in e else e)
    check("e", got_times == expected_times,
          f"timeline times {got_times}")
    check("e2", len(flat) == 8, f"timeline entries {len(flat)}")
    # no invented decision: timeline must not claim EU/MOFCOM/UK outcomes
    bad_tl = [e for e in flat
              if any(s in e for s in ["agreed", "decided", "approved",
                                      "reached a deal", "passed"])]
    check("e3", not bad_tl, f"timeline no invented outcomes {bad_tl}")

    # (f) region counts
    regions = getattr(m, "REGIONS", [])
    expected = {"Asia-Pacific": 7, "Americas": 5, "Europe": 10,
                "Africa": 0, "Oceania": 0, "Middle East": 4, "World": 2}
    got = dict(regions)
    check("f", got == expected, f"regions {got}")
    check("f2", sum(got.values()) == 28, f"total {sum(got.values())}")
    # cross-check: leads + briefs per region match REGIONS
    from collections import Counter
    cnt = Counter()
    lead_regions = ["Americas", "Europe", "Americas", "Europe",
                    "Asia-Pacific", "Europe", "Europe", "Asia-Pacific",
                    "Europe", "Middle East", "Asia-Pacific", "Europe",
                    "Middle East"]
    for r in lead_regions:
        cnt[r] += 1
    for (_, r) in briefs:
        cnt[r] += 1
    cnt_full = {name: cnt.get(name, 0) for name in expected}
    check("f3", cnt_full == expected, f"stories per region {cnt_full}")

    # (g) DATE CHECK 41 items
    dc = getattr(m, "DATECHECK", [])
    check("g", len(dc) == 41, f"DATE CHECK items {len(dc)}")
    bad_dc = [x for x in dc if not x or "..." in x]
    check("g2", not bad_dc, f"DATE CHECK complete {bad_dc}")

    # (h) pictorial bands: content + shading
    if im is not None:
        # lead pictorial bands y 177-213, 3 cards
        bands = [(17, 340), (350, 673), (684, 1007)]
        ok = True
        det = []
        for (x0, x1) in bands:
            vals = set()
            for y in range(177, 213):
                for x in range(x0, x1):
                    vals.add(im.getpixel((x, y))[0] // 16)
            det.append(len(vals))
            if len(vals) < 3:
                ok = False
        check("h", ok, f"lead pictorial brightness levels {det}")
        # medium pictorial strips exist (non-cream rows in y 339-353)
        strip_vals = set()
        for y in range(339, 353):
            for x in range(17, 1007, 7):
                strip_vals.add(im.getpixel((x, y))[0] // 32)
        check("h2", len(strip_vals) >= 3,
              f"medium pictorial strip levels {len(strip_vals)}")
        # no bright flame-orange leak into the timeline band
        leak = 0
        for y in range(138, 176):
            for x in range(1024):
                r, g, b = im.getpixel((x, y))[:3]
                if r > 230 and 100 < g < 200 and b < 90:
                    leak += 1
        check("h3", leak == 0, f"flame-orange pixels in timeline: {leak}")

    # (i) README badges
    readme_p = os.path.join(HERE, "README.md")
    if os.path.exists(readme_p):
        with open(readme_p) as f:
            rd = f.read()
        slug = "news-image-20261126"
        repo = "mekzibnn/news-world-today-26"
        b1 = f"https://make.fun/badge/{slug}.svg"
        b2 = f"https://make.fun/badge/{slug}/{repo}/rank.svg"
        b3 = f"https://make.fun/badge/{slug}/{repo}/reward.svg"
        check("i", b1 in rd, "badge competition")
        check("i2", b2 in rd, "badge rank")
        check("i3", b3 in rd, "badge reward (with owner/repo)")
        check("i4", "shields.io" not in rd, "no shields.io")
        check("i5", "https://make.fun/bounty/news-image-20261126" in rd,
              "badge links to bounty")
    else:
        check("i", False, "README.md missing")

    # (j) no '...' in main.py
    check("j", "..." not in src, "no '...' in main.py")

    # (k) main.py rules: no top-level Pillow import; honours output env; fallback
    lines = src.splitlines()
    top_import = any(
        re.match(r"^(from PIL|import PIL)", ln) for ln in lines)
    check("k", not top_import, "no top-level Pillow import")
    check("k2", "MAKEFUN_OUTPUT_DIR" in src, "honours $MAKEFUN_OUTPUT_DIR")
    check("k3", "ENTRY_OUTPUT" in src, "honours $ENTRY_OUTPUT")
    check("k4", "/output/entry.png" in src, "falls back to /output/entry.png")
    check("k5", "shutil.copyfile" in src, "fallback copies committed entry.png")

    # (l) fact traps (must NOT appear as Thursday news)
    bad_facts = []
    if "Macy" in src and "parade" in src.lower():
        # parade must be postponed, never 'runs Thursday'
        if re.search(r"parade (runs|held|takes place|marches) (on )?Thursday",
                     src, re.I):
            bad_facts.append("parade runs Thursday")
    if "Barreto" in src and "Thursday" in src:
        # Barreto must not be presented as a Thursday appearance
        if re.search(r"Barreto.*Thursday|Thursday.*Barreto", src):
            bad_facts.append("Barreto Thursday")
    check("l", not bad_facts, f"fact traps {bad_facts}")
    # Wednesday numbers must not be presented as Thursday closes
    check("l2", "$3,645" not in src, "no Tue gold $3,645 as Thu")
    check("l3", "3,645" not in src or "Tuesday" in src or "Selasa" in src,
          "gold 3645 only as Tuesday context")

    print(f"\n{len(PASS)} PASS, {len(FAIL)} FAIL")
    if FAIL:
        print("FAILURES:", FAIL)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
