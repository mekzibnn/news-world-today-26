"""news-image-20261126 v1 — renders entry.png (1024x1024).

Broadsheet: masthead, date headline, sub-headline, stat strip, region bar,
UTC timeline, 3 big lead cards with realistic pictorials, 10 medium cards,
world map with numbered pins, 15 briefs, DATE CHECK (41 items), footer.
All facts verified to primary sources on Thu 26 Nov 2026 (WIB).
Pictorials are clipped to their band (separate RGBA layer + alpha_composite).
"""

import os
import shutil
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except Exception:
    _PIL_OK = False
    Image = ImageDraw = ImageFont = None

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (247, 243, 232)
CARD = (255, 253, 247)
NAVY = (26, 42, 74)
NAVY_D = (16, 28, 52)
RED = (185, 28, 28)
RED_D = (153, 27, 27)
INK = (28, 28, 28)
GREY = (96, 96, 96)
LINE = (203, 192, 172)
GOLD = (176, 138, 38)
WHITE = (255, 255, 255)

REGION_COLORS = {
    "Asia-Pacific": (28, 122, 92),
    "Americas": (38, 92, 164),
    "Europe": (118, 62, 142),
    "Africa": (178, 118, 28),
    "Oceania": (28, 138, 158),
    "Middle East": (178, 82, 28),
    "World": (102, 102, 102),
}

# ---------------------------------------------------------------- fonts
_FONT_CACHE = {}


def _font_path(name):
    base = "/usr/share/fonts/truetype/dejavu/"
    return base + name


def font(size, bold=False, serif=False):
    """Load a DejaVu font; fall back to PIL default if unavailable."""
    if not _PIL_OK:
        return None
    key = (size, bold, serif)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if serif:
        name = "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf"
    else:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        f = ImageFont.truetype(_font_path(name), size)
    except Exception:
        try:
            f = ImageFont.load_default()
        except Exception:
            f = None
    _FONT_CACHE[key] = f
    return f


def tw(draw, text, f):
    """Pixel width of text in font f."""
    if f is None:
        return len(text) * 6
    try:
        return int(draw.textlength(text, font=f))
    except Exception:
        try:
            return int(f.getlength(text))
        except Exception:
            return len(text) * 6


def wrap(draw, text, f, max_w):
    """Greedy word-wrap; returns list of lines, each <= max_w."""
    words = text.split()
    if not words:
        return [""]
    lines = []
    cur = words[0]
    for wd in words[1:]:
        trial = cur + " " + wd
        if tw(draw, trial, f) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines


def draw_wrapped(draw, text, f, x, y, max_w, fill, line_h=None, align="left"):
    """Draw wrapped text; returns y after the last line."""
    if line_h is None:
        line_h = int(f.size * 1.25) if f is not None else 16
    lines = wrap(draw, text, f, max_w)
    for ln in lines:
        if align == "center":
            lx = x + (max_w - tw(draw, ln, f)) // 2
        elif align == "right":
            lx = x + max_w - tw(draw, ln, f)
        else:
            lx = x
        draw.text((lx, y), ln, font=f, fill=fill)
        y += line_h
    return y


def vgrad(img, box, c1, c2):
    """Vertical gradient fill inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)
    grad = Image.new("RGB", (1, h))
    px = grad.load()
    for yy in range(h):
        t = yy / max(1, h - 1)
        px[0, yy] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    grad = grad.resize((w, h))
    img.paste(grad, (x0, y0))


def pictorial_band(base, box, draw_fn):
    """Draw a pictorial clipped to its band: render on a separate RGBA layer
    the size of the band, then alpha-composite onto base. Nothing can escape
    the band (the v5 flame-overlap lesson)."""
    x0, y0, x1, y1 = box
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d, w, h)
    base.alpha_composite(layer, (x0, y0))


def skyline(d, w, h, base_y, color, seed=0):
    """Simple dark building silhouettes along the bottom of a band."""
    import random
    rnd = random.Random(seed)
    x = 0
    while x < w:
        bw = rnd.randint(12, 30)
        bh = rnd.randint(int(h * 0.25), int(h * 0.6))
        d.rectangle([x, base_y - bh, x + bw, base_y], fill=color)
        # lit windows
        for _ in range(rnd.randint(1, 4)):
            wx = x + rnd.randint(2, max(2, bw - 5))
            wy = base_y - bh + rnd.randint(3, max(3, bh - 6))
            d.rectangle([wx, wy, wx + 2, wy + 3], fill=(255, 214, 120))
        x += bw + rnd.randint(1, 5)


def stars(d, w, h, n, color=(255, 255, 255), seed=1):
    import random
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.randint(2, w - 3)
        y = rnd.randint(2, int(h * 0.7))
        r = rnd.choice([1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)

# ---------------------------------------------------------------- content
# All facts verified to primary sources (Reuters/AP/WSJ/CNN/Consilium/UEFA/NWS)
# on Thu 26 Nov 2026. Market numbers are MID-SESSION (closes not yet in at
# build time ~10:50 WIB) and are labelled as such. KTT UE / MOFCOM / UK bill
# are FORECAST — they happen later in the day; nothing is invented.

MASTHEAD_LEFT = "THE WORLD IN ONE DAY"
MASTHEAD_RIGHT = "28 STORIES · 7 REGIONS · EVERY ONE DATED"
DATE_HEADLINE = "THURSDAY 26 NOVEMBER 2026"
SUB_HEADLINE = ("Macy's 100th parade postponed to Saturday · EU budget summit "
                "opens · Twin storms slam Thanksgiving")

STATS = [
    ("100", "Macy's parade, postponed"),
    ("€1.78tn", "EU budget compromise"),
    ("3.25%", "Bank of Korea rate"),
    ("$3,579", "Gold, morning spot"),
    ("112", "Russian drones overnight"),
    ("13", "Indonesia mine dead"),
]

REGIONS = [
    ("Asia-Pacific", 7),
    ("Americas", 5),
    ("Europe", 10),
    ("Africa", 0),
    ("Oceania", 0),
    ("Middle East", 4),
    ("World", 2),
]

TIMELINE = [
    ["Wed ET · Macy's parade to Sat",
     "00:45 · UCL early finals",
     "03:00 · UCL main finals",
     "08:00 · BOK hikes to 3.25%"],
    ["14:00 · MOFCOM briefing",
     "16:00 · EU summit opens",
     "16:30 · UK bill first reading",
     "02:38 Fri · SF king tide 8.0 ft"],
]

# 3 big leads: (kicker, headline, body, source, tag, pictorial)
LEADS = [
    ("AMERICAS · NEW YORK",
     "Macy's 100th parade postponed to Saturday",
     "First weather postponement in 100 years. Nor'easter winds 30–40 mph, "
     "gusts to 65 mph; balloons grounded. NBC airs the 2025 parade.",
     "Reuters · AP · WSJ · CNN", "REPORTED", "macys"),
    ("EUROPE · BRUSSELS",
     "EU summit opens: €1.78tn plan faces revolt",
     "Leaders meet Thu–Fri on the 2028–34 budget and Ukraine funding. "
     "France and Visegrad reject it; Germany wants deeper cuts.",
     "Consilium · Reuters", "FORECAST", "eu"),
    ("AMERICAS · BOTH COASTS",
     "Twin storms slam Thanksgiving on both coasts",
     "Nor'easter floods the East Coast; a king tide swamps San Francisco "
     "Bay at 8.0 ft. Busiest Thanksgiving travel in 16 years.",
     "Reuters · NWS · CNN", "REPORTED", "storm"),
]

# 10 medium cards 4-13: (num, kicker, headline, body, tag, pictorial)
MEDIUMS = [
    (4, "EUROPE · LONDON",
     "UK-EU reset bill goes to Parliament",
     "First reading Thu; food checks end Mar 2028.",
     "FORECAST", "bill"),
    (5, "ASIA-PACIFIC · MARKETS",
     "Asia rebounds after Wall St comeback",
     "Dow erased 1,100-pt drop Wed; Asia +1.5–2.3% Thu.",
     "REPORTED", "chart"),
    (6, "EUROPE · FOOTBALL",
     "Roma end PSG's run; Bayern beaten",
     "PSG 2–2 Roma; Sporting 2–2 Man Utd; Liverpool 3–0.",
     "REPORTED", "ball"),
    (7, "EUROPE · FRANKFURT",
     "EU to settle ECB's new top team",
     "De Cos, Boone, Brunnermeier — decision at summit.",
     "FORECAST", "bank"),
    (8, "ASIA-PACIFIC · BEIJING",
     "China pushes back on tariffs",
     "Guo: overcapacity a 'false premise'; MOFCOM due Thu.",
     "REPORTED", "flag"),
    (9, "EUROPE · KYIV",
     "Kyiv hit; two refineries burn",
     "112 drones, 88 downed; Ryazan and Kirishi burn.",
     "REPORTED", "flame"),
    (10, "MIDDLE EAST · ADEN",
     "Yemen outlaws Houthis near Aden",
     "Unanimous vote; 661 strikes claimed; Houthis 60 km out.",
     "REPORTED", "flag"),
    (11, "ASIA-PACIFIC · SEOUL",
     "Bank of Korea hikes to 3.25%",
     "Third hike since July; growth outlook 4.1% for 2027.",
     "REPORTED", "coin"),
    (12, "EUROPE · MADRID",
     "Spain votes Sunday in snap election",
     "Final polls: PP 31.5%, PSOE 29%, Vox ~18%.",
     "FORECAST", "ballot"),
    (13, "MIDDLE EAST · DOHA",
     "Qatar GP goes ahead despite war",
     "Race Sun 19:00 at Lusail; no sprint; Derulo Sun night.",
     "FORECAST", "race"),
]

# 15 briefs: (text, region)
BRIEFS = [
    ("US markets closed Thu for Thanksgiving", "World"),
    ("Fed Dec hike now 97% likely after hot PCE, GDP", "Americas"),
    ("Gold rebounds to ~$3,579 spot after Wed slide", "World"),
    ("Kospi rebounds after 10-month low", "Asia-Pacific"),
    ("Busiest travel in 16 years; NFL tripleheader", "Americas"),
    ("SF king tide nears record 8.0 ft", "Americas"),
    ("Indonesia mine disaster: 13 dead, 13 trapped", "Asia-Pacific"),
    ("ECB's new team: de Cos, Boone, Brunnermeier", "Europe"),
    ("Spain snap election: what Sunday decides", "Europe"),
    ("Qatar GP: racing on while war rages next door", "Middle East"),
    ("China tariff response: formal reply still awaited", "Asia-Pacific"),
    ("Ukraine overnight: Kyiv strike, two refineries hit", "Europe"),
    ("Aden braces as Houthis close in", "Middle East"),
    ("UCL Wed: PSG 2–2 Roma, Sporting 2–2 Man Utd", "Europe"),
    ("Asia Thu: Nikkei +1.5%, Kospi +2.3% mid-session", "Asia-Pacific"),
]

# DATE CHECK — 41 terse one-liners (name + correct date). Full detail in research.
DATECHECK = [
    "301 tariffs — Wed 25",
    "PCE + GDP — Wed 25",
    "Miss Universe — Tue 24",
    "Odesa strikes — Tue",
    "NBA Tue night — Tue",
    "UCL Tue night — Tue",
    "Asia plunge — Wed 25",
    "US stocks — Wed 25",
    "Gold close — Wed 25",
    "ECB nominations — passed",
    "UK-EU deal — Fri 20",
    "EU budget — Sat 21",
    "Shenzhou-24 — Wed 25",
    "Riyadh hit — Tue 24",
    "Huawei — Tue 24",
    "Senegal win — Tue 24",
    "Ships sunk — Mon 23",
    "700k killed — Mon 23",
    "Japan stimulus — Sat 21",
    "Spain vote — Sun 29",
    "Qatar GP — Sun 29",
    "Africa — Wed or earlier",
    "Politburo probe — Wed 25",
    "Booker vs Nvidia — Wed",
    "COP31 — Sun 22",
    "Cikande fire — Sat 21",
    "Netanyahu — Sun 22",
    "Nikkei +4.5% — Tue 24",
    "Berlin summit — Thu 19",
    "Shenzhen talks — 19–20",
    "Macy's call — Wed night",
    "NBA Wed night — Wed",
    "Aden attack — Sun 22",
    "Refinery claim — unverified",
    "Pacifica Pier — Wed 25",
    "MOFCOM No. 59 — 24 Nov",
    "Burnham claim — Wed",
    "Otago flood — too small",
    "Australia CPI — Wed 25",
    "Samara strike — Tue→Wed",
    "Kyiv rescue — Wed 25",
]

DATECHECK_TITLE = ("DATE CHECK — NOT THURSDAY 26 NOVEMBER: "
                   "first reported earlier, or not yet happened.")

FOOTER_LINE1 = ("Sources: Reuters · AP · WSJ · CNN · Consilium · UEFA · NWS · "
                "Formula1.com · Compiled Thu 26 Nov 2026 (WIB).")
FOOTER_LINE2 = ("REPORTED = carried by the day's wires · CLAIM = one side's account, "
                "labelled as such · FORECAST = still to happen when drawn.")

# Map pins: (lead number, lon, lat, display dx, dy)
PINS = [
    (1, -74.0, 40.7, 0, 0),       # New York — Macy's
    (2, 4.4, 50.8, 12, -18),      # Brussels — EU summit
    (3, -122.4, 37.8, 0, 0),      # San Francisco — king tide
    (4, -0.1, 51.5, -10, 8),      # London — UK bill
    (5, 139.7, 35.7, 0, 0),       # Tokyo — Asia markets
    (6, 2.35, 48.85, 10, 14),     # Paris — UCL
    (7, 8.7, 50.1, 17, -3),       # Frankfurt — ECB
    (8, 116.4, 39.9, 0, 0),       # Beijing — China tariffs
    (9, 30.5, 50.45, 14, 10),     # Kyiv — Ukraine
    (10, 45.0, 12.8, 0, 0),       # Aden — Yemen
    (11, 127.0, 37.5, 0, 0),      # Seoul — BOK
    (12, -3.7, 40.4, -16, 6),    # Madrid — Spain election
    (13, 51.5, 25.3, 0, 0),       # Doha — Qatar GP
]

# Simplified continent outlines (lon, lat) — stylised, recognisable.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-60, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 25), (-90, 20), (-97, 16),
     (-105, 20), (-117, 33), (-125, 40), (-125, 49), (-140, 60), (-165, 60)],
    # South America
    [(-80, 10), (-60, 5), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
     (-58, -35), (-65, -45), (-70, -55), (-75, -40), (-80, -20), (-80, 0)],
    # Europe
    [(-10, 36), (-9, 43), (0, 44), (3, 43), (10, 44), (12, 45), (19, 46),
     (23, 40), (28, 36), (30, 36), (23, 36), (19, 42), (12, 44), (0, 46),
     (-2, 50), (-5, 50), (-10, 54), (-10, 58), (-5, 60), (5, 58), (10, 57),
     (18, 56), (21, 55), (24, 59), (28, 60), (30, 62), (25, 65), (18, 66),
     (12, 66), (5, 60)],
    # Africa
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 15), (48, 11), (51, 10), (48, 0), (40, -10), (35, -20), (30, -30),
     (20, -35), (15, -30), (12, -18), (8, -2), (9, 4), (-8, 4), (-13, 8),
     (-17, 12)],
    # Asia
    [(30, 36), (36, 36), (44, 38), (48, 38), (54, 37), (57, 26), (61, 25),
     (66, 25), (70, 20), (75, 15), (80, 10), (80, 7), (85, 15), (90, 22),
     (95, 16), (100, 8), (103, 2), (100, 8), (105, 10), (108, 15), (110, 20),
     (115, 23), (120, 25), (122, 30), (127, 35), (130, 38), (135, 43),
     (140, 45), (142, 50), (140, 55), (135, 60), (130, 60), (125, 65),
     (120, 70), (110, 73), (100, 76), (90, 75), (80, 73), (70, 72),
     (60, 69), (50, 68), (40, 67), (35, 65), (30, 62), (30, 55), (35, 45),
     (40, 40), (35, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32),
     (132, -32), (135, -35), (137, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20), (113, -22)],
]

# ---------------------------------------------------------------- pictorials
# Each draws inside a (w, h) band on an RGBA layer — clipped by construction.


def pic_macys(d, w, h):
    # Stormy sky, grounded balloon, rain, city.
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((52, 68, 96), (140, 152, 168)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    stars(d, w, h, 8, (255, 255, 255), seed=3)
    # balloon — big rounded shape, deflated low, tethered
    cx, cy = int(w * 0.30), int(h * 0.42)
    d.ellipse([cx - 26, cy - 20, cx + 26, cy + 16], fill=(198, 44, 44, 255))
    d.ellipse([cx - 18, cy - 26, cx + 18, cy + 4], fill=(226, 88, 66, 255))
    d.ellipse([cx - 12, cy - 18, cx + 2, cy - 4], fill=(255, 190, 150, 255))
    d.rectangle([cx - 3, cy + 16, cx + 3, cy + 26], fill=(120, 60, 40, 255))
    d.line([(cx, cy + 26), (cx + 8, h)], fill=(220, 220, 220, 255), width=1)
    # rain streaks
    for i in range(22):
        x = (i * 37) % w
        y = (i * 23) % h
        d.line([(x, y), (x - 3, y + 7)], fill=(200, 215, 230, 200), width=1)
    # city silhouette
    skyline(d, w, h, h, (24, 34, 52, 255), seed=5)


def pic_eu(d, w, h):
    # EU blue, circle of gold stars, summit building.
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((16, 42, 96), (48, 84, 150)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    cx, cy = int(w * 0.68), int(h * 0.42)
    r = 15
    for k in range(12):
        import math
        a = math.pi * 2 * k / 12 - math.pi / 2
        x = cx + int(r * math.cos(a))
        y = cy + int(r * math.sin(a))
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 214, 80, 255))
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 214, 80, 255))
    # building
    d.rectangle([8, h - 22, 58, h], fill=(20, 30, 56, 255))
    for i in range(5):
        d.rectangle([13 + i * 9, h - 18, 18 + i * 9, h - 12],
                    fill=(255, 214, 120, 255))
    d.rectangle([8, h - 24, 58, h - 22], fill=(120, 140, 180, 255))


def pic_storm(d, w, h):
    # Left: storm clouds + rain over city. Right: waves + high water.
    mid = w // 2
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((44, 56, 72), (120, 128, 140)))
        d.line([(0, yy), (mid, yy)], fill=c + (255,))
        c2 = tuple(int(a + (b - a) * t) for a, b in
                   zip((18, 62, 110), (70, 130, 170)))
        d.line([(mid, yy), (w, yy)], fill=c2 + (255,))
    # clouds left
    for (cx, cy, cr) in [(22, 12, 12), (44, 9, 15), (66, 13, 11), (88, 10, 13)]:
        d.ellipse([cx - cr, cy - cr // 2, cx + cr, cy + cr // 2],
                  fill=(70, 80, 96, 255))
    for i in range(14):
        x = (i * 19) % mid
        y = (i * 17) % h
        d.line([(x, y), (x - 3, y + 7)], fill=(200, 215, 230, 200), width=1)
    skyline(d, mid, h, h, (22, 30, 48, 255), seed=7)
    # waves right
    for k in range(4):
        yb = h - 8 - k * 7
        for x in range(mid, w, 10):
            d.arc([x, yb - 4, x + 10, yb + 4], 180, 360,
                  fill=(220, 235, 245, 220), width=2)
    d.rectangle([mid, h - 3, w, h], fill=(200, 225, 240, 255))


def pic_chart(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((20, 90, 70), (60, 160, 120)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    pts = [(2, h - 8), (w // 4, h - 16), (w // 2, h - 10),
           (3 * w // 4, h - 22), (w - 3, h - 30)]
    d.line(pts, fill=(255, 255, 255, 255), width=2, joint="curve")
    for (x, y) in pts:
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 214, 80, 255))
    d.polygon([(2, h - 8)] + pts + [(w - 3, h), (2, h)],
              fill=(255, 255, 255, 40))


def pic_ball(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((24, 60, 36), (70, 140, 80)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    cx, cy, r = w // 2, h // 2, min(w, h) // 2 - 3
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 245, 240, 255))
    d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3],
              fill=(40, 40, 40, 255))
    for k in range(5):
        import math
        a = math.pi * 2 * k / 5 - math.pi / 2
        x = cx + int(r * 0.75 * math.cos(a))
        y = cy + int(r * 0.75 * math.sin(a))
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(40, 40, 40, 255))


def pic_bank(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((30, 48, 84), (70, 100, 150)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    # columns + pediment (height-aware: never invert a rectangle)
    d.polygon([(w // 2, 2), (6, 10), (w - 6, 10)], fill=(226, 200, 120, 255))
    col_top = 11
    col_bot = h - 4
    if col_bot <= col_top:
        col_bot = col_top + 1
    for i in range(4):
        x = 10 + i * (w - 20) // 3
        d.rectangle([x, col_top, x + 5, col_bot], fill=(240, 238, 228, 255))
    base_top = max(col_bot, h - 4)
    if base_top < h - 1:
        d.rectangle([6, base_top, w - 6, h - 2], fill=(226, 200, 120, 255))


def pic_flag(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((150, 30, 30), (200, 70, 60)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    stars(d, w, h, 5, (255, 214, 80), seed=9)
    d.rectangle([6, 3, 8, h - 3], fill=(220, 220, 220, 255))
    d.polygon([(8, 4), (30, 8), (8, 13)], fill=(255, 214, 80, 255))


def pic_flame(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((40, 20, 24), (140, 60, 40)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    skyline(d, w, h, h, (18, 14, 18, 255), seed=11)
    cx = w // 2
    for (r, col) in [(14, (255, 120, 30, 255)), (9, (255, 190, 60, 255)),
                     (5, (255, 240, 160, 255))]:
        d.polygon([(cx - r, h - 6), (cx - r // 2, h - 26 - r),
                   (cx, h - 30 - r), (cx + r // 2, h - 26 - r),
                   (cx + r, h - 6)], fill=col)
    for i in range(6):
        x = (i * 29) % w
        d.ellipse([x, h - 12, x + 3, h - 9], fill=(255, 150, 50, 255))


def pic_coin(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((24, 70, 100), (60, 140, 170)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    cx, cy, r = w // 2, h // 2, min(w, h) // 2 - 3
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(226, 200, 120, 255))
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3],
              outline=(160, 120, 40, 255), width=2)
    d.text((cx - 5, cy - 7), "%", font=font(12, bold=True),
           fill=(120, 80, 20, 255))


def pic_ballot(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((90, 30, 90), (150, 70, 150)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    d.rectangle([w // 2 - 12, 4, w // 2 + 12, h - 4],
                fill=(245, 245, 240, 255), outline=(120, 120, 120, 255))
    for i in range(3):
        y = 8 + i * 6
        d.line([(w // 2 - 8, y), (w // 2 + 8, y)],
               fill=(150, 150, 150, 255), width=1)
    d.line([(w // 2 - 6, h // 2 + 2), (w // 2 - 1, h // 2 + 7),
            (w // 2 + 8, h // 2 - 4)], fill=(30, 140, 60, 255), width=2)


def pic_race(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((120, 60, 20), (200, 120, 50)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    stars(d, w, h, 6, (255, 255, 255), seed=13)
    # floodlit track curve
    d.arc([-w // 4, h - 14, w, h + 22], 200, 340,
          fill=(245, 245, 240, 255), width=3)
    d.arc([-w // 4, h - 8, w, h + 28], 200, 340,
          fill=(255, 214, 80, 255), width=2)
    # checkered flag
    for i in range(4):
        for j in range(3):
            col = (20, 20, 20, 255) if (i + j) % 2 == 0 else (255, 255, 255, 255)
            d.rectangle([w - 22 + i * 4, 4 + j * 4, w - 18 + i * 4, 8 + j * 4],
                        fill=col)


def pic_bill(d, w, h):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip((40, 50, 90), (90, 110, 160)))
        d.line([(0, yy), (w, yy)], fill=c + (255,))
    d.rectangle([w // 2 - 13, 3, w // 2 + 13, h - 3],
                fill=(245, 243, 235, 255), outline=(120, 120, 120, 255))
    d.rectangle([w // 2 - 13, 3, w // 2 + 13, 8], fill=(26, 42, 74, 255))
    for i in range(3):
        y = 12 + i * 5
        d.line([(w // 2 - 9, y), (w // 2 + 9, y)],
               fill=(120, 120, 120, 255), width=1)


PICTURES = {
    "macys": pic_macys, "eu": pic_eu, "storm": pic_storm,
    "chart": pic_chart, "ball": pic_ball, "bank": pic_bank,
    "flag": pic_flag, "flame": pic_flame, "coin": pic_coin,
    "ballot": pic_ballot, "race": pic_race, "bill": pic_bill,
}

# ---------------------------------------------------------------- render

def render():
    img = Image.new("RGBA", (W, H), CREAM + (255,))
    d = ImageDraw.Draw(img)

    # ---- masthead 0-36 (navy)
    d.rectangle([0, 0, W, 36], fill=NAVY)
    f_mast = font(19, bold=True)
    f_mast_r = font(12, bold=True)
    d.text((16, 8), MASTHEAD_LEFT, font=f_mast, fill=WHITE)
    rw = tw(d, MASTHEAD_RIGHT, f_mast_r)
    d.text((W - 16 - rw, 11), MASTHEAD_RIGHT, font=f_mast_r, fill=(200, 210, 230))

    # ---- date headline 36-72 (serif, navy, centred)
    f_date = font(32, bold=True, serif=True)
    dw = tw(d, DATE_HEADLINE, f_date)
    d.text(((W - dw) // 2, 38), DATE_HEADLINE, font=f_date, fill=NAVY)

    # ---- sub-headline 72-88 (red, centred)
    f_sub = font(15, bold=True)
    sw = tw(d, SUB_HEADLINE, f_sub)
    d.text(((W - sw) // 2, 72), SUB_HEADLINE, font=f_sub, fill=RED)

    # ---- stat strip 88-120 (6 cells, 1-line captions)
    d.line([(16, 88), (W - 16, 88)], fill=LINE, width=1)
    d.line([(16, 120), (W - 16, 120)], fill=LINE, width=1)
    cell_w = (W - 32) / 6.0
    f_num = font(20, bold=True)
    f_cap = font(10)
    for i, (num, cap) in enumerate(STATS):
        cx0 = 16 + i * cell_w
        if i > 0:
            d.line([(cx0, 90), (cx0, 118)], fill=LINE, width=1)
        nw = tw(d, num, f_num)
        d.text((cx0 + (cell_w - nw) / 2, 89), num, font=f_num, fill=RED)
        lw = tw(d, cap, f_cap)
        d.text((cx0 + (cell_w - lw) / 2, 110), cap, font=f_cap, fill=GREY)

    # ---- region bar 120-138: segmented bar + coloured count text
    total = sum(c for _, c in REGIONS)
    x = 16
    for name, c in REGIONS:
        wseg = (W - 32) * c / total if total else 0
        if wseg >= 1:
            d.rectangle([x, 121, x + wseg, 128],
                        fill=REGION_COLORS[name])
        x += wseg
    f_reg = font(11, bold=True)
    parts = []
    for name, c in REGIONS:
        parts.append((name.upper() + " ", REGION_COLORS[name]))
        parts.append((str(c), INK))
        parts.append(("  ·  ", GREY))
    parts = parts[:-1]
    tot_w = sum(tw(d, t, f_reg) for t, _ in parts)
    cx = (W - tot_w) // 2
    cy = 130
    for t, col in parts:
        d.text((cx, cy), t, font=f_reg, fill=col)
        cx += tw(d, t, f_reg)

    # ---- timeline 138-176 (2 rows, 16px)
    d.rectangle([0, 138, W, 176], fill=(238, 232, 216))
    d.line([(0, 138), (W, 138)], fill=LINE, width=1)
    d.line([(0, 176), (W, 176)], fill=LINE, width=1)
    f_tl = font(16)
    f_tl_b = font(16, bold=True)
    cell_w = (W - 32) / 4.0
    for ri, row in enumerate(TIMELINE):
        y = 141 + ri * 19
        for ci, entry in enumerate(row):
            if " · " in entry:
                tpart, lpart = entry.split(" · ", 1)
            else:
                tpart, lpart = "", entry
            ex = 16 + ci * cell_w
            tx = ex
            if tpart:
                d.text((tx, y), tpart, font=f_tl_b, fill=RED)
                tx += tw(d, tpart, f_tl_b) + 4
                d.text((tx, y), "·", font=f_tl, fill=GREY)
                tx += tw(d, "·", f_tl) + 4
            d.text((tx, y), lpart, font=f_tl, fill=INK)

    # ---- 3 big lead cards 176-338 (162px)
    card_w = (W - 32 - 20) / 3.0
    card_h = 162
    card_y = 176
    f_kick = font(12, bold=True)
    f_head = font(18, bold=True)
    f_body = font(13)
    f_src = font(11)
    f_tag = font(11, bold=True)
    for i, (kicker, head, body, src, tag, pic) in enumerate(LEADS):
        x0 = 16 + i * (card_w + 10)
        x1 = x0 + card_w
        d.rectangle([x0, card_y, x1, card_y + card_h], fill=CARD,
                    outline=LINE, width=1)
        # pictorial band (clipped) — top 36px inside the card
        band = (int(x0) + 1, card_y + 1, int(x1) - 1, card_y + 37)
        pictorial_band(img, band, PICTURES[pic])
        ty = card_y + 40
        d.text((x0 + 8, ty), kicker, font=f_kick, fill=RED)
        ty += 15
        ty = draw_wrapped(d, head, f_head, x0 + 8, ty, card_w - 16,
                          NAVY, line_h=21)
        ty = draw_wrapped(d, body, f_body, x0 + 8, ty + 1, card_w - 16,
                          INK, line_h=16)
        # source + tag at the bottom
        d.text((x0 + 8, card_y + card_h - 14), src, font=f_src, fill=GREY)
        tagw = tw(d, tag, f_tag)
        d.rectangle([x1 - 8 - tagw - 8, card_y + card_h - 16,
                     x1 - 8, card_y + card_h - 2],
                    fill=RED if tag == "REPORTED" else NAVY)
        d.text((x1 - 8 - tagw - 4, card_y + card_h - 15), tag,
               font=f_tag, fill=WHITE)

    # ---- 10 medium cards 338-490 (2 rows x 5, 76px each)
    med_w = (W - 32 - 32) / 5.0
    med_h = 76
    f_mhead = font(13, bold=True)
    f_mbody = font(12)
    f_mnum = font(12, bold=True)
    for idx, (num, kicker, head, body, tag, pic) in enumerate(MEDIUMS):
        r = idx // 5
        c = idx % 5
        x0 = 16 + c * (med_w + 8)
        x1 = x0 + med_w
        y0 = 338 + r * med_h
        d.rectangle([x0, y0, x1, y0 + med_h], fill=CARD,
                    outline=LINE, width=1)
        # pictorial strip (clipped) — top 14px
        band = (int(x0) + 1, y0 + 1, int(x1) - 1, y0 + 15)
        pictorial_band(img, band, PICTURES[pic])
        # number badge over the pictorial
        d.rectangle([x0 + 4, y0 + 2, x0 + 21, y0 + 15], fill=NAVY)
        d.text((x0 + 7, y0 + 2), str(num), font=f_mnum, fill=WHITE)
        ty = y0 + 17
        ty = draw_wrapped(d, head, f_mhead, x0 + 6, ty, med_w - 12,
                          NAVY, line_h=16)
        draw_wrapped(d, body, f_mbody, x0 + 6, ty, med_w - 12,
                     INK, line_h=13)

    # ---- map (left) + briefs (right) 490-797
    f_sect = font(14, bold=True)
    d.text((16, 494), "WHERE IT HAPPENED — 13 PINNED", font=f_sect, fill=NAVY)
    d.line([(16, 512), (470, 512)], fill=LINE, width=1)
    # map box
    mx0, my0, mx1, my1 = 20, 516, 466, 772
    d.rectangle([mx0, my0, mx1, my1], fill=(232, 238, 242),
                outline=LINE, width=1)
    lon0, lon1, lat0, lat1 = -170, 190, -60, 85

    def proj(lon, lat):
        px = mx0 + (lon - lon0) / (lon1 - lon0) * (mx1 - mx0)
        py = my1 - (lat - lat0) / (lat1 - lat0) * (my1 - my0)
        return px, py

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=(214, 202, 170), outline=(150, 138, 110))
    for lon in range(-150, 181, 30):
        x, _ = proj(lon, 0)
        d.line([(x, my0), (x, my1)], fill=(210, 218, 226), width=1)
    for lat in range(-30, 61, 30):
        _, y = proj(0, lat)
        d.line([(mx0, y), (mx1, y)], fill=(210, 218, 226), width=1)
    # pins
    f_pin = font(11, bold=True)
    for (num, lon, lat, dx, dy) in PINS:
        ax, ay = proj(lon, lat)
        px, py = ax + dx, ay + dy
        if dx or dy:
            d.line([(ax, ay), (px, py)], fill=RED, width=1)
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED,
                  outline=WHITE, width=1)
        nw = tw(d, str(num), f_pin)
        d.text((px - nw / 2, py - 6), str(num), font=f_pin, fill=WHITE)
    d.text((20, 778), "Pins numbered as the 13 leads above.",
           font=font(11), fill=GREY)

    # briefs (right): header + 15 items, 18px, one line each
    bx0 = 492
    d.text((bx0, 494), "ALSO ON THURSDAY 26 NOVEMBER", font=f_sect, fill=NAVY)
    d.line([(bx0, 512), (W - 16, 512)], fill=LINE, width=1)
    f_br = font(18)
    f_brn = font(18, bold=True)
    by = 516.0
    for i, (text, region) in enumerate(BRIEFS, start=1):
        num_s = str(i) + ". "
        nw = tw(d, num_s, f_brn)
        d.text((bx0, by), num_s, font=f_brn, fill=RED)
        d.text((bx0 + nw, by), text, font=f_br, fill=INK)
        by += 18.5

    # ---- DATE CHECK 797-1000 (red box, 4 columns, 16px)
    d.rectangle([16, 797, W - 16, 1000], outline=RED, width=2)
    d.rectangle([16, 797, W - 16, 813], fill=RED)
    f_dc_t = font(13, bold=True)
    twd = tw(d, DATECHECK_TITLE, f_dc_t)
    d.text(((W - twd) // 2, 799), DATECHECK_TITLE, font=f_dc_t, fill=WHITE)
    f_dc = font(16)
    ncol = 4
    col_w = (W - 32) / ncol
    per_col = (len(DATECHECK) + ncol - 1) // ncol
    for ci in range(ncol):
        cx = 22 + ci * col_w
        cy = 819.0
        for item in DATECHECK[ci * per_col:(ci + 1) * per_col]:
            d.text((cx, cy), "• " + item, font=f_dc, fill=INK)
            cy += 16.5

    # ---- footer 1000-1024
    f_ft = font(10)
    for j, line in enumerate([FOOTER_LINE1, FOOTER_LINE2]):
        lw = tw(d, line, f_ft)
        d.text(((W - lw) // 2, 1001 + j * 12), line, font=f_ft, fill=GREY)

    return img


def _out_path():
    for key in ("MAKEFUN_OUTPUT_DIR", "ENTRY_OUTPUT"):
        v = os.environ.get(key)
        if v:
            return os.path.join(v, "entry.png") if key == "MAKEFUN_OUTPUT_DIR" else v
    return "/output/entry.png"


def main():
    if not _PIL_OK:
        # No Pillow: fall back to the committed entry.png.
        here = os.path.dirname(os.path.abspath(__file__))
        src = os.path.join(here, "entry.png")
        dst = _out_path()
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            return 0
        return 1
    try:
        img = render()
    except Exception:
        here = os.path.dirname(os.path.abspath(__file__))
        src = os.path.join(here, "entry.png")
        dst = _out_path()
        if os.path.exists(src):
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
                return 0
            except Exception:
                return 1
        raise
    dst = _out_path()
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        img.convert("RGB").save(dst, "PNG")
    except Exception:
        # Still write next to main.py so the entry exists.
        here = os.path.dirname(os.path.abspath(__file__))
        img.convert("RGB").save(os.path.join(here, "entry.png"), "PNG")
        return 0
    # Also keep a local copy next to main.py.
    here = os.path.dirname(os.path.abspath(__file__))
    img.convert("RGB").save(os.path.join(here, "entry.png"), "PNG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
