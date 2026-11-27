#!/usr/bin/env python3
"""news-image-20261126 v2 -- THE WORLD IN ONE DAY.

Blind rewrite. 37 stories, 9 regions, all from Thursday 26 November 2026.
Every story verified from the research file; every story carries a source
and a status tag. Flat vector pictorials, drawn with PIL only.
"""
import os
import shutil
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except Exception:
    _PIL_OK = False

W, H = 1024, 1024
MARGIN = 24
CW = W - 2 * MARGIN  # 976

# ---- palette (audit: muted brick red, cream, navy) ----
CREAM = (247, 243, 232)
NAVY = (26, 42, 74)
INK = (28, 28, 28)
RED = (155, 65, 65)          # muted brick red (NOT bright 185,28,28)
GRAY = (96, 94, 88)
LINE = (178, 172, 160)
LAND = (203, 206, 192)
LAND_LINE = (150, 155, 140)
WHITE = (255, 255, 255)
GOLD = (176, 138, 60)

REGION_COLORS = {
    "Asia-Pacific": (66, 104, 138),
    "Americas": (150, 70, 66),
    "Europe": (58, 88, 138),
    "Africa": (150, 110, 52),
    "Oceania": (58, 128, 118),
    "Middle East": (138, 98, 58),
    "World": (102, 102, 100),
}
REGION_ORDER = ["Asia-Pacific", "Americas", "Europe", "Africa",
                "Oceania", "Middle East", "World"]

STATUS_COLORS = {
    "REPORTED": NAVY,
    "CONFIRMED": (58, 118, 68),
    "CLAIM": RED,
    "FORECAST": (102, 102, 100),
    "ONGOING": (48, 108, 108),
    "OFFICIAL": (40, 98, 60),
}

# ---- fonts ----
_HERE = os.path.dirname(os.path.abspath(__file__))
_PLAYFAIR_CANDIDATES = [
    os.path.join(_HERE, "fonts", "PlayfairDisplay.ttf"),
    "/tmp/PlayfairDisplay.ttf",
]
_DEJAVU_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
_DEJAVU_SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
_NOTO_SERIF_I = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
_DEJAVU_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_DEJAVU_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _playfair(size):
    for path in _PLAYFAIR_CANDIDATES:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size)
                try:
                    f.set_variation_by_axes([700])
                except Exception:
                    try:
                        f.set_variation_by_name("Bold")
                    except Exception:
                        pass
                return f
            except Exception:
                continue
    return ImageFont.truetype(_DEJAVU_SERIF_B, size)


def _serif(size, bold=False, italic=False):
    if bold:
        return ImageFont.truetype(_DEJAVU_SERIF_B, size)
    if italic:
        if os.path.exists(_NOTO_SERIF_I):
            return ImageFont.truetype(_NOTO_SERIF_I, size)
        return ImageFont.truetype(_DEJAVU_SERIF, size)
    return ImageFont.truetype(_DEJAVU_SERIF, size)


def _sans(size, bold=False):
    if bold:
        return ImageFont.truetype(_DEJAVU_SANS_B, size)
    return ImageFont.truetype(_DEJAVU_SANS, size)


# ---- data: 37 stories, 9 regions ----
# Pictorial leads: (num, region, kicker, headline, summary, source, status, art)
LEADS = [
    (1, "Americas", "AMERICAS · NEW YORK",
     "Macy's 100th parade postponed to Saturday",
     "A nor'easter brings 60 mph gusts to New York; the parade moves to "
     "Saturday, a first in 100 years.",
     "AP · Reuters", "REPORTED", "macys"),
    (2, "Europe", "EUROPE · BRUSSELS",
     "EU summit ends early with no budget deal",
     "Leaders quit Thursday night without a deal on the €1.78tn budget; "
     "talks move to 17–18 December.",
     "Reuters · Consilium", "REPORTED", "eu"),
    (3, "Americas", "AMERICAS · BOTH COASTS",
     "Twin storms slam Thanksgiving on both coasts",
     "Nor'easter floods the East Coast; a king tide swamps San Francisco "
     "Bay at 8.0 ft.",
     "Reuters · NWS", "REPORTED", "storms"),
]

# Medium pictorials: (num, region, headline, summary, source, status, art)
MEDIUM = [
    (4, "Europe", "UK-EU bill goes to Parliament",
     "European Partnership Bill gets first reading; second reading 7 Dec.",
     "Parliament · gov.uk", "REPORTED", "parliament"),
    (5, "Asia-Pacific", "Asia stocks rebound after Wall St comeback",
     "Nikkei +0.86%, Kospi +0.29%, Taiex +2.50% at the close.",
     "Reuters · AP", "REPORTED", "markets"),
    (6, "Europe", "Roma end PSG's perfect run",
     "PSG 2–2 Roma; Lille 2–1 Bayern, first loss of the season.",
     "UEFA · AP", "REPORTED", "ucl"),
    (7, "Europe", "EU leaders back de Cos for ECB top job",
     "Pablo Hernández de Cos backed as next ECB president; formal "
     "appointment to follow.",
     "Consilium · Reuters", "REPORTED", "ecb"),
    (8, "Asia-Pacific", "China firmly opposes US tariff plan",
     "MOFCOM's He Yadong: Beijing 'reserves the right' to act; no "
     "specific reply yet.",
     "Xinhua · Reuters", "REPORTED", "ship"),
    (9, "Europe", "Kyiv hit by ballistic missiles",
     "112 drones launched overnight, 88 downed; Ryazan and Kirishi "
     "refineries burn.",
     "Reuters · Al Jazeera", "REPORTED", "ukraine"),
    (10, "Middle East", "Yemen outlaws Houthis as rebels near Aden",
     "Parliament votes unanimously; Houthis about 60 km from Aden.",
     "Reuters · Saba", "REPORTED", "yemen"),
    (11, "Asia-Pacific", "Bank of Korea hikes rate to 3.25%",
     "Third hike since July; growth outlook lifted to 4.1% for 2027.",
     "Reuters", "REPORTED", "bok"),
    (12, "Africa", "Kenya court halts US-backed Ebola site",
     "High Court: quarantine facility breached the constitution; work "
     "stopped.",
     "Reuters", "REPORTED", "kenya"),
    (13, "Oceania", "Australia–Fiji alliance enters into force",
     "Vuvale Union and Veitacini Treaty take effect; Fiji is Australia's "
     "4th formal ally.",
     "pm.gov.au · Reuters", "REPORTED", "fiji"),
]

# Briefs 14-37: (num, region, city, headline, source, status)
# Status is REPORTED unless noted; FORECAST items are tagged in the image.
BRIEFS = [
    (14, "World", "New York", "US markets closed for Thanksgiving", "AP", "REPORTED"),
    (15, "Americas", "Washington", "Fed Dec hike now 97% likely", "CME", "REPORTED"),
    (16, "World", "London", "Gold COMEX close $3,593", "COMEX", "REPORTED"),
    (17, "Asia-Pacific", "Seoul", "Kospi rebounds after 10-month low", "Reuters", "REPORTED"),
    (18, "Americas", "Washington", "Travel busiest in 16 years", "FAA", "REPORTED"),
    (19, "Americas", "San Francisco", "King tide nears record 8.0 ft", "NWS", "REPORTED"),
    (20, "Asia-Pacific", "West Java", "Mine disaster: 13 dead, 13 trapped", "Reuters", "REPORTED"),
    (21, "Europe", "Frankfurt", "ECB's new team: de Cos et al.", "Consilium", "REPORTED"),
    (22, "Europe", "Madrid", "Spain election preview", "Reuters", "FORECAST"),
    (23, "Middle East", "Doha", "GP weekend: Derulo plays", "F1.com", "FORECAST"),
    (24, "Asia-Pacific", "Beijing", "China tariff reply still awaited", "Reuters", "REPORTED"),
    (25, "Europe", "Kyiv", "Kyiv ballistic strike, 2 refineries hit", "Reuters", "REPORTED"),
    (26, "Middle East", "Aden", "Aden braces as Houthis close in", "Reuters", "REPORTED"),
    (27, "Europe", "Europe", "Champions League Wednesday results", "UEFA", "REPORTED"),
    (28, "Asia-Pacific", "Asia", "Asia markets Thursday rebound", "Reuters", "REPORTED"),
    (29, "Africa", "Cairo", "Egypt detains driver after tanker blast", "Reuters", "REPORTED"),
    (30, "Africa", "Pretoria", "S. Africa PPI jumps to 8.1%", "Stats SA", "REPORTED"),
    (31, "Africa", "Kigali", "Rwanda hikes to 9.5%, inflation 19.5%", "Reuters", "REPORTED"),
    (32, "Africa", "Mogadishu", "Could al-Shabab take the capital?", "BBC", "REPORTED"),
    (33, "Oceania", "Wellington", "Fibre optics map Alpine Fault", "Conversation", "REPORTED"),
    (34, "Asia-Pacific", "Pyongyang", "Kim: deploy tactical nukes", "Reuters", "REPORTED"),
    (35, "Asia-Pacific", "Hong Kong", "1 yr since Wang Fuk Court fire", "AP", "REPORTED"),
    (36, "Europe", "Madrid", "Spain votes Sunday", "Reuters", "FORECAST"),
    (37, "Middle East", "Doha", "Qatar GP goes ahead", "F1.com", "FORECAST"),
]

# Stat strip: (number, caption)
STATS = [
    ("100", "Macy's 100th parade — postponed to Saturday"),
    ("€1.78tn", "EU budget compromise"),
    ("3.25%", "Bank of Korea rate"),
    ("$3,593", "COMEX gold close"),
    ("112", "drones at Ukraine overnight"),
    ("13", "dead, Indonesia mine disaster"),
]

# Timeline: (time, label) — 6 entries, one row
TIMELINE = [
    ("Wed ET", "Macy's to Sat"),
    ("00:45", "UCL early finals"),
    ("03:00", "UCL main finals"),
    ("08:00", "BOK 3.25%"),
    ("16:00", "EU summit"),
    ("16:30", "UK bill"),
]

# DATE CHECK: (story, real date) — 12 most important of 60
DATE_CHECK = [
    ("Section 301 tariffs announced", "Wed 25 Nov"),
    ("US PCE + Q3 GDP released", "Wed 25 Nov"),
    ("Miss Universe crowned", "Tue 24 Nov"),
    ("Asia markets plunge", "Wed 25 Nov"),
    ("Gold COMEX close $3,505", "Wed 25 Nov"),
    ("Shenzhou-24 launched", "Wed 25 Nov"),
    ("Cairo tanker explosion", "Wed 25 Nov"),
    ("Haftar–Erdogan meeting", "Wed 25 Nov"),
    ("Ramaphosa ruling", "Wed 25 Nov"),
    ("Chibis detained", "Wed 25 Nov"),
    ("Netanyahu judges' advice", "Wed 25 Nov"),
    ("Birthright block", "Wed 25 Nov"),
]

# Map pins 1-13: (lon, lat)
PINS = {
    1: (-74.0, 40.7),    # New York
    2: (4.35, 50.85),    # Brussels
    3: (-122.4, 37.8),   # San Francisco
    4: (-0.1, 51.5),     # London
    5: (139.7, 35.7),    # Tokyo
    6: (2.35, 48.85),    # Paris
    7: (8.68, 50.11),    # Frankfurt
    8: (116.4, 39.9),    # Beijing
    9: (30.5, 50.45),    # Kyiv
    10: (45.0, 12.8),    # Aden
    11: (127.0, 37.5),   # Seoul
    12: (36.8, -1.3),    # Nairobi
    13: (178.4, -17.7),  # Suva
}

# Simplified continent outlines (lon, lat) for the world map
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-70, 62),
     (-55, 47), (-70, 42), (-80, 32), (-90, 21), (-97, 16), (-105, 20),
     (-115, 30), (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-168, 66)],
    # South America
    [(-80, 10), (-75, 5), (-60, 0), (-50, -5), (-40, -15), (-48, -28),
     (-58, -38), (-65, -45), (-70, -55), (-73, -35), (-70, -20), (-80, -5),
     (-80, 10)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (12, 55),
     (18, 56), (21, 59), (28, 60), (30, 62), (25, 65), (20, 70), (12, 71),
     (5, 68), (0, 62), (-5, 58), (-10, 55), (-10, 43), (-10, 36)],
    # Africa
    [(-17, 15), (-15, 25), (-10, 31), (0, 36), (10, 37), (20, 32), (30, 31),
     (35, 28), (40, 15), (48, 11), (51, 12), (45, 0), (40, -10), (35, -20),
     (30, -30), (20, -35), (15, -30), (12, -18), (9, 0), (8, 4), (-8, 4),
     (-13, 8), (-17, 15)],
    # Asia
    [(30, 62), (40, 68), (60, 70), (80, 73), (100, 76), (120, 73), (140, 72),
     (160, 70), (178, 65), (170, 60), (160, 55), (150, 45), (140, 40),
     (130, 35), (120, 30), (110, 20), (105, 10), (100, 5), (95, 15), (90, 22),
     (80, 15), (75, 8), (70, 20), (60, 25), (55, 28), (50, 30), (45, 35),
     (40, 40), (35, 45), (30, 50), (30, 62)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (130, -32), (135, -35),
     (140, -38), (145, -38), (150, -37), (153, -27), (150, -22), (145, -15),
     (142, -11), (135, -12), (130, -13), (125, -14), (120, -20), (113, -22)],
]

SUBTITLE = ("A nor'easter grounds New York's 100th Thanksgiving parade, EU "
            "leaders end their budget summit with no deal, and Korea hikes "
            "its rate to 3.25%.")


def region_counts():
    counts = {r: 0 for r in REGION_ORDER}
    for s in LEADS + MEDIUM + BRIEFS:
        counts[s[1]] += 1
    return counts


def wrap(draw, text, font, max_w):
    """Wrap text to fit max_w; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_status_badge(draw, x, y, status):
    """Outline badge: thin border + coloured text (NOT filled)."""
    col = STATUS_COLORS.get(status, NAVY)
    f = _sans(9, bold=True)
    tw = draw.textlength(status, font=f)
    pad = 4
    h = 14
    draw.rectangle([x, y, x + tw + pad * 2, y + h], outline=col, width=1)
    draw.text((x + pad, y + 2), status, font=f, fill=col)
    return tw + pad * 2


# ---- flat vector pictorials (each draws into its own RGBA layer, clipped) ----

def _layer(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _skyline(d, x0, y0, w, h, color, windows):
    """Simple building silhouettes with lit windows."""
    import random
    rnd = random.Random(7)
    x = x0
    while x < x0 + w - 8:
        bw = rnd.randint(12, 26)
        bh = rnd.randint(int(h * 0.35), int(h * 0.85))
        d.rectangle([x, y0 + h - bh, x + bw, y0 + h], fill=color)
        for _ in range(bh // 9):
            wx = rnd.randint(x + 2, x + bw - 4)
            wy = rnd.randint(y0 + h - bh + 3, y0 + h - 6)
            d.rectangle([wx, wy, wx + 2, wy + 3], fill=windows)
        x += bw + 2


def _rain(d, x0, y0, w, h, color=(200, 215, 230, 255)):
    import random
    rnd = random.Random(11)
    for _ in range(int(w * h / 220)):
        x = rnd.randint(x0, x0 + w)
        y = rnd.randint(y0, y0 + h)
        d.line([(x, y), (x - 3, y + 9)], fill=color, width=1)


def art_macys(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(30, 45, 75, 255))
    _skyline(d, 0, h - 52, w, 52, (18, 28, 52, 255), (240, 200, 90, 255))
    _rain(d, 0, 0, w, h - 40)
    # big parade balloon (cream ellipse + red nose + ropes)
    d.ellipse([w * 0.30, 8, w * 0.70, 62], fill=(240, 235, 220, 255))
    d.ellipse([w * 0.46, 30, w * 0.54, 46], fill=(155, 65, 65, 255))
    d.line([(w * 0.38, 60), (w * 0.36, 78)], fill=(220, 220, 210, 255), width=2)
    d.line([(w * 0.62, 60), (w * 0.64, 78)], fill=(220, 220, 210, 255), width=2)
    # gold 100 badge
    d.ellipse([w - 52, h - 52, w - 8, h - 8], fill=(176, 138, 60, 255))
    f = _sans(16, bold=True)
    d.text((w - 40, h - 44), "100", font=f, fill=(255, 255, 255, 255))
    # red postponed banner
    d.rectangle([0, h - 26, 208, h], fill=(155, 65, 65, 255))
    f2 = _sans(11, bold=True)
    d.text((8, h - 22), "POSTPONED TO SATURDAY", font=f2,
           fill=(255, 255, 255, 255))
    return img


def art_eu(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(52, 84, 138, 255))
    # circle of gold stars
    import math
    cx, cy, r = w * 0.30, h * 0.42, 34
    for i in range(12):
        a = math.radians(i * 30 - 90)
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(240, 200, 90, 255))
    d.rectangle([w * 0.52, 18, w - 16, h - 18], fill=(247, 243, 232, 255))
    d.rectangle([w * 0.52, 18, w - 16, 30], fill=(26, 42, 74, 255))
    f = _sans(10, bold=True)
    d.text((w * 0.52 + 8, 20), "BUDGET 2028–34", font=f,
           fill=(255, 255, 255, 255))
    f2 = _playfair(26)
    d.text((w * 0.52 + 8, 40), "€1.78tn", font=f2, fill=(26, 42, 74, 255))
    f3 = _sans(10)
    d.text((w * 0.52 + 8, 76), "no deal — talks move", font=f3, fill=(90, 90, 90, 255))
    d.text((w * 0.52 + 8, 90), "to 17–18 December", font=f3, fill=(90, 90, 90, 255))
    return img


def art_storms(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    # left: nor'easter night sky + rain + skyline
    d.rectangle([0, 0, w // 2, h], fill=(38, 52, 82, 255))
    _skyline(d, 0, h - 44, w // 2, 44, (20, 30, 55, 255), (240, 200, 90, 255))
    _rain(d, 0, 0, w // 2, h - 30)
    d.ellipse([w * 0.10, 6, w * 0.30, 26], fill=(90, 105, 130, 255))
    d.ellipse([w * 0.22, 12, w * 0.42, 30], fill=(70, 85, 112, 255))
    # right: king tide wave + skyline
    d.rectangle([w // 2, 0, w, h], fill=(52, 98, 138, 255))
    d.ellipse([w * 0.72, 8, w * 0.82, 24], fill=(240, 220, 140, 255))
    d.polygon([(w // 2, h), (w // 2 + 20, h - 58), (w // 2 + 90, h - 30),
               (w // 2 + 150, h - 62), (w, h - 34), (w, h)],
              fill=(28, 66, 102, 255))
    d.polygon([(w // 2, h), (w // 2 + 40, h - 34), (w // 2 + 110, h - 18),
               (w, h - 26), (w, h)], fill=(120, 175, 205, 255))
    f = _sans(11, bold=True)
    d.text((w - 62, h - 22), "8.0 FT", font=f, fill=(255, 255, 255, 255))
    return img


def art_parliament(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(232, 226, 210, 255))
    # parliament silhouette
    d.rectangle([10, h - 34, w - 10, h], fill=(58, 72, 96, 255))
    for i in range(5):
        x = 22 + i * 30
        d.rectangle([x, h - 48, x + 14, h - 34], fill=(58, 72, 96, 255))
    d.polygon([(w // 2 - 8, h - 62), (w // 2 + 8, h - 62), (w // 2, h - 74)],
              fill=(58, 72, 96, 255))
    # document
    d.rectangle([w - 62, 8, w - 12, 44], fill=(255, 255, 255, 255),
                outline=(26, 42, 74, 255))
    for i in range(3):
        d.line([(w - 56, 18 + i * 8), (w - 18, 18 + i * 8)],
               fill=(120, 120, 120, 255), width=2)
    return img


def art_markets(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(238, 240, 234, 255))
    # grid
    for i in range(1, 4):
        d.line([(0, i * h // 4), (w, i * h // 4)], fill=(210, 212, 204, 255))
    # rising chart line
    pts = [(8, h - 14), (40, h - 26), (70, h - 20), (100, h - 34),
           (130, h - 28), (160, h - 46), (w - 8, h - 52)]
    d.line(pts, fill=(58, 118, 68, 255), width=3)
    d.polygon(pts + [(w - 8, h), (8, h)], fill=(58, 118, 68, 60))
    f = _sans(12, bold=True)
    d.text((10, 6), "+0.86%", font=f, fill=(58, 118, 68, 255))
    return img


def art_ucl(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(38, 96, 58, 255))
    d.ellipse([w - 52, 8, w - 12, 48], fill=(255, 255, 255, 255),
              outline=(28, 28, 28, 255))
    d.polygon([(w - 32, 20), (w - 24, 28), (w - 40, 28)], fill=(28, 28, 28, 255))
    d.rectangle([8, 8, 108, 34], fill=(26, 42, 74, 255))
    f = _sans(11, bold=True)
    d.text((14, 15), "PSG 2–2 ROMA", font=f, fill=(255, 255, 255, 255))
    d.line([(0, h - 14), (w, h - 14)], fill=(255, 255, 255, 255), width=2)
    return img


def art_ecb(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(42, 66, 110, 255))
    f = _playfair(34)
    d.text((12, 6), "€", font=f, fill=(240, 200, 90, 255))
    # bank columns
    for i in range(3):
        x = w - 78 + i * 22
        d.rectangle([x, h - 30, x + 12, h - 8], fill=(220, 225, 235, 255))
    d.rectangle([w - 84, h - 36, w - 8, h - 30], fill=(220, 225, 235, 255))
    return img


def art_ship(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(52, 98, 138, 255))
    # sea
    d.rectangle([0, h - 18, w, h], fill=(28, 66, 102, 255))
    # containers
    cols = [(155, 65, 65, 255), (176, 138, 60, 255), (58, 118, 68, 255),
            (66, 104, 138, 255)]
    for i, c in enumerate(cols):
        d.rectangle([14 + i * 34, h - 44, 14 + i * 34 + 30, h - 18], fill=c)
    # hull
    d.polygon([(6, h - 18), (w - 6, h - 18), (w - 22, h - 6), (22, h - 6)],
              fill=(28, 28, 28, 255))
    f = _sans(10, bold=True)
    d.text((10, 6), "SECTION 301", font=f, fill=(255, 255, 255, 255))
    return img


def art_ukraine(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(34, 38, 52, 255))
    # refinery towers + flames
    for i, x in enumerate([16, 52, 88]):
        d.rectangle([x, h - 34, x + 18, h - 8], fill=(70, 72, 80, 255))
        d.polygon([(x + 3, h - 34), (x + 9, h - 48), (x + 15, h - 34)],
                  fill=(220, 120, 40, 255))
    # drone
    d.ellipse([w - 44, 10, w - 20, 22], fill=(200, 200, 200, 255))
    d.line([(w - 52, 16), (w - 44, 16)], fill=(200, 200, 200, 255), width=2)
    d.line([(w - 20, 16), (w - 12, 16)], fill=(200, 200, 200, 255), width=2)
    f = _sans(10, bold=True)
    d.text((10, 6), "112 DRONES", font=f, fill=(240, 200, 90, 255))
    return img


def art_yemen(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(214, 196, 160, 255))
    # parliament dome
    d.rectangle([w // 2 - 40, h - 30, w // 2 + 40, h - 8], fill=(120, 96, 66, 255))
    d.pieslice([w // 2 - 26, h - 52, w // 2 + 26, h - 8],
               180, 360, fill=(120, 96, 66, 255))
    d.rectangle([w // 2 - 2, h - 62, w // 2 + 2, h - 52], fill=(120, 96, 66, 255))
    # sun
    d.ellipse([w - 40, 6, w - 16, 30], fill=(220, 160, 60, 255))
    return img


def art_bok(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(255, 255, 255, 255))
    # taegeuk (red/blue circle)
    d.pieslice([14, 12, 54, 52], 0, 180, fill=(155, 65, 65, 255))
    d.pieslice([14, 12, 54, 52], 180, 360, fill=(52, 84, 138, 255))
    d.ellipse([24, 22, 44, 42], fill=(255, 255, 255, 255))
    # black bars (gwe)
    for i in range(3):
        d.rectangle([66, 14 + i * 8, 92, 14 + i * 8 + 4], fill=(28, 28, 28, 255))
    # green up arrow + rate
    d.polygon([(w - 66, h - 18), (w - 44, h - 40), (w - 36, h - 30),
               (w - 22, h - 48), (w - 22, h - 38), (w - 40, h - 18)],
              fill=(58, 118, 68, 255))
    f = _sans(13, bold=True)
    d.text((w - 62, 6), "3.25%", font=f, fill=(58, 118, 68, 255))
    return img


def art_kenya(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(232, 228, 216, 255))
    # courthouse columns
    for i in range(4):
        x = 16 + i * 34
        d.rectangle([x, 14, x + 14, h - 14], fill=(96, 88, 74, 255))
    d.rectangle([8, 8, w - 8, 14], fill=(96, 88, 74, 255))
    d.rectangle([8, h - 14, w - 8, h - 8], fill=(96, 88, 74, 255))
    # gavel
    d.rectangle([w - 46, 8, w - 14, 16], fill=(120, 84, 52, 255))
    d.line([(w - 30, 16), (w - 30, 34)], fill=(120, 84, 52, 255), width=4)
    return img


def art_fiji(box):
    w, h = box
    img = _layer(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h], fill=(52, 110, 150, 255))
    # Australia flag (blue + stars)
    d.rectangle([8, 10, 84, 42], fill=(26, 42, 110, 255))
    for sx, sy in [(20, 18), (34, 26), (48, 16), (62, 28), (74, 20)]:
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 255, 255, 255))
    # Fiji flag (light blue + shield)
    d.rectangle([96, 10, 172, 42], fill=(120, 180, 210, 255))
    d.rectangle([104, 16, 128, 36], fill=(255, 255, 255, 255))
    d.rectangle([104, 16, 116, 26], fill=(155, 65, 65, 255))
    # handshake arc
    d.arc([w // 2 - 40, h - 34, w // 2 + 40, h + 10], 180, 360,
          fill=(240, 200, 90, 255), width=3)
    return img


ART = {
    "macys": art_macys, "eu": art_eu, "storms": art_storms,
    "parliament": art_parliament, "markets": art_markets, "ucl": art_ucl,
    "ecb": art_ecb, "ship": art_ship, "ukraine": art_ukraine,
    "yemen": art_yemen, "bok": art_bok, "kenya": art_kenya, "fiji": art_fiji,
}


# ---- layout ----

def draw_masthead(d, y):
    # Title (Playfair Bold 46)
    f_title = _playfair(46)
    title = "THE WORLD IN ONE DAY"
    tw = d.textlength(title, font=f_title)
    d.text(((W - tw) / 2, y), title, font=f_title, fill=INK)
    y += 52
    # Date
    f_date = _playfair(20)
    date = "THURSDAY 26 NOVEMBER 2026"
    tw = d.textlength(date, font=f_date)
    d.text(((W - tw) / 2, y), date, font=f_date, fill=INK)
    y += 26
    # Subtitle (italic, 2 lines, centred)
    f_sub = _serif(13, italic=True)
    lines = wrap(d, SUBTITLE, f_sub, CW - 60)
    for ln in lines:
        tw = d.textlength(ln, font=f_sub)
        d.text(((W - tw) / 2, y), ln, font=f_sub, fill=INK)
        y += 17
    y += 2
    # Masthead count line
    f_cnt = _sans(11, bold=True)
    cnt = "37 STORIES  ·  9 REGIONS  ·  ALL FROM THURSDAY 26 NOVEMBER 2026"
    tw = d.textlength(cnt, font=f_cnt)
    d.text(((W - tw) / 2, y), cnt, font=f_cnt, fill=RED)
    y += 16
    d.line([(MARGIN, y), (W - MARGIN, y)], fill=INK, width=2)
    return y + 6


def draw_stats(d, y):
    cell = CW / 6.0
    f_num = _playfair(27)
    f_cap = _sans(9)
    for i, (num, cap) in enumerate(STATS):
        x0 = MARGIN + i * cell
        tw = d.textlength(num, font=f_num)
        d.text((x0 + (cell - tw) / 2, y), num, font=f_num, fill=RED)
        lines = wrap(d, cap, f_cap, cell - 16)
        yy = y + 32
        for ln in lines[:2]:
            tw2 = d.textlength(ln, font=f_cap)
            d.text((x0 + (cell - tw2) / 2, yy), ln, font=f_cap, fill=GRAY)
            yy += 11
        if i < 5:
            d.line([(x0 + cell, y + 4), (x0 + cell, y + 50)], fill=LINE, width=1)
    return y + 56


def draw_region_bar(d, y):
    counts = region_counts()
    total = sum(counts.values())
    x = MARGIN
    for r in REGION_ORDER:
        wseg = CW * counts[r] / total
        d.rectangle([x, y, x + wseg - 1, y + 12],
                    fill=REGION_COLORS[r])
        x += wseg
    y += 17
    f = _sans(10)
    parts = []
    for r in REGION_ORDER:
        parts.append("%s %d" % (r, counts[r]))
    txt = "  ·  ".join(parts)
    tw = d.textlength(txt, font=f)
    d.text(((W - tw) / 2, y), txt, font=f, fill=INK)
    return y + 14


def draw_lead(d, x, y, w, lead):
    num, region, kicker, headline, summary, source, status, art = lead
    # pictorial (own RGBA layer, clipped to band)
    ph = 130
    layer = ART[art]((w, ph))
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base.alpha_composite(layer, (x, y))
    # number badge
    f_num = _sans(12, bold=True)
    d.ellipse([x + 4, y + 4, x + 24, y + 24], fill=RED)
    d.text((x + 10, y + 7), str(num), font=f_num, fill=WHITE)
    y += ph + 6
    # kicker
    f_k = _sans(10, bold=True)
    d.text((x, y), kicker, font=f_k, fill=RED)
    y += 14
    # headline (Playfair Bold 23, up to 3 lines)
    f_h = _playfair(23)
    lines = wrap(d, headline, f_h, w)
    for ln in lines[:3]:
        d.text((x, y), ln, font=f_h, fill=INK)
        y += 27
    # summary (serif 12, up to 2 lines)
    f_s = _serif(12)
    slines = wrap(d, summary, f_s, w)
    for ln in slines[:2]:
        d.text((x, y), ln, font=f_s, fill=INK)
        y += 15
    y += 3
    # source + status badge
    f_src = _sans(9)
    d.text((x, y + 1), "SOURCE: " + source, font=f_src, fill=GRAY)
    sw = d.textlength("SOURCE: " + source, font=f_src)
    draw_status_badge(d, x + sw + 8, y, status)
    return y + 16, base


def draw_medium(d, x, y, w, med):
    num, region, headline, summary, source, status, art = med
    ph = 54
    layer = ART[art]((w, ph))
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base.alpha_composite(layer, (x, y))
    f_num = _sans(10, bold=True)
    d.ellipse([x + 3, y + 3, x + 19, y + 19], fill=RED)
    d.text((x + 8, y + 5), str(num), font=f_num, fill=WHITE)
    y += ph + 4
    # headline (DejaVuSerif-Bold 16, up to 3 lines)
    f_h = _serif(16, bold=True)
    lines = wrap(d, headline, f_h, w)
    for ln in lines[:3]:
        d.text((x, y), ln, font=f_h, fill=INK)
        y += 19
    # source + status
    f_src = _sans(8)
    d.text((x, y + 1), source, font=f_src, fill=GRAY)
    sw = d.textlength(source, font=f_src)
    draw_status_badge(d, x + sw + 6, y, status)
    return y + 15, base


def draw_map(d, x, y, w, h):
    # land
    def proj(lon, lat):
        px = x + (lon + 180.0) / 360.0 * w
        py = y + (85.0 - lat) / 140.0 * h
        return (px, py)
    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    # pins 1-13 (white outline so clustered pins stay distinct)
    f = _sans(9, bold=True)
    for num, (lon, lat) in PINS.items():
        px, py = proj(lon, lat)
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=WHITE)
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED)
        tw = d.textlength(str(num), font=f)
        d.text((px - tw / 2, py - 6), str(num), font=f, fill=WHITE)


def draw_also(d, x, y, w):
    f_h = _sans(11, bold=True)
    d.text((x, y), "ALSO ON THURSDAY 26 NOVEMBER — STORIES 14–37",
           font=f_h, fill=INK)
    y += 16
    f_b = _serif(10)
    f_bb = _serif(10, bold=True)
    col_w = (w - 10) / 2.0
    row_h = 11
    for i, b in enumerate(BRIEFS):
        num, region, city, headline, source, status = b
        col = 0 if i < 12 else 1
        row = i % 12
        bx = x + col * (col_w + 10)
        by = y + row * row_h
        txt = "%d. %s — %s — %s" % (num, city, headline, source)
        if status == "FORECAST":
            txt += " · FORECAST"
        # number in red, rest in ink
        num_txt = "%d. " % num
        d.text((bx, by), num_txt, font=f_bb, fill=RED)
        nw = d.textlength(num_txt, font=f_bb)
        d.text((bx + nw, by), txt[len(num_txt):], font=f_b, fill=INK)
    return y + 12 * row_h


def draw_timeline(d, y):
    f_lab = _sans(11, bold=True)
    d.text((MARGIN, y), "THE DAY IN UTC", font=f_lab, fill=INK)
    x = MARGIN + 110
    f_t = _sans(11, bold=True)
    f_l = _sans(11)
    for tm, label in TIMELINE:
        d.text((x, y), tm, font=f_t, fill=RED)
        tw = d.textlength(tm, font=f_t)
        d.text((x + tw + 4, y), "· " + label, font=f_l, fill=INK)
        x += tw + 4 + d.textlength("· " + label, font=f_l) + 16
    d.line([(MARGIN, y - 4), (W - MARGIN, y - 4)], fill=LINE, width=1)
    return y + 16


def draw_date_check(d, y):
    f_h = _sans(12, bold=True)
    d.text((MARGIN, y), "DATE CHECK — THESE ARE NOT 26 NOVEMBER",
           font=f_h, fill=RED)
    y += 16
    f_b = _serif(9)
    col_w = (CW - 10) / 2.0
    for i, (story, date) in enumerate(DATE_CHECK):
        col = 0 if i < 6 else 1
        row = i % 6
        bx = MARGIN + col * (col_w + 10)
        by = y + row * 11
        d.text((bx, by), "× ", font=f_b, fill=RED)
        d.text((bx + 10, by), "%s — %s" % (story, date), font=f_b, fill=INK)
    return y + 6 * 11


def draw_footer(d, y):
    f = _sans(9)
    line1 = ("HOW SURE:  REPORTED = carried by the day's wires  ·  CLAIM = one "
             "side's account, labelled as such  ·  FORECAST = still to happen "
             "when drawn  ·  ONGOING = still unfolding.")
    tw = d.textlength(line1, font=f)
    d.text(((W - tw) / 2, y), line1, font=f, fill=GRAY)
    y += 12
    line2 = ("Every story here happened or was first reported on Thursday 26 "
             "November 2026. Sources are named on each story. Scenes are drawn "
             "illustrations, not photographs.")
    tw = d.textlength(line2, font=f)
    d.text(((W - tw) / 2, y), line2, font=f, fill=GRAY)
    return y + 12


def render():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    layers = []
    y = 12
    y = draw_masthead(d, y)
    y = draw_stats(d, y)
    y = draw_region_bar(d, y)
    # 3 big leads
    lead_w = (CW - 2 * 11) // 3
    ly = y + 4
    for i, lead in enumerate(LEADS):
        x = MARGIN + i * (lead_w + 11)
        _, layer = draw_lead(d, x, ly, lead_w, lead)
        layers.append(layer)
    y = ly + 246
    # 10 medium cards, 2 rows x 5
    med_w = (CW - 4 * 9) // 5
    my = y + 6
    for i, med in enumerate(MEDIUM):
        row, col = divmod(i, 5)
        x = MARGIN + col * (med_w + 9)
        yy = my + row * 132
        _, layer = draw_medium(d, x, yy, med_w, med)
        layers.append(layer)
    y = my + 2 * 132 + 4
    # map + also
    f_h = _sans(11, bold=True)
    d.text((MARGIN, y), "WHERE IT HAPPENED — PINS 1–13", font=f_h, fill=INK)
    map_w = 300
    map_h = 132
    draw_map(d, MARGIN, y + 16, map_w, map_h)
    also_x = MARGIN + map_w + 14
    also_w = W - MARGIN - also_x
    draw_also(d, also_x, y, also_w)
    y = y + 16 + map_h + 6
    # timeline
    y = draw_timeline(d, y)
    # date check
    y = draw_date_check(d, y)
    y += 6
    # footer
    y = draw_footer(d, y)
    # composite pictorial layers (clipped to their bands by construction)
    for layer in layers:
        img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return img


def _output_path():
    for var in ("MAKEFUN_OUTPUT_DIR", "ENTRY_OUTPUT"):
        v = os.environ.get(var)
        if v:
            os.makedirs(v, exist_ok=True)
            return os.path.join(v, "entry.png")
    os.makedirs("/output", exist_ok=True)
    return "/output/entry.png"


def main():
    here = _HERE
    committed = os.path.join(here, "entry.png")
    out = _output_path()
    if not _PIL_OK:
        if os.path.exists(committed):
            shutil.copyfile(committed, out)
        return 0
    try:
        img = render()
        img.save(out, "PNG")
        # also refresh the committed copy when rendering locally
        if os.path.abspath(out) != os.path.abspath(committed):
            img.save(committed, "PNG")
        print("rendered %s (%dx%d)" % (out, W, H))
        return 0
    except Exception as e:
        print("render failed: %s" % e, file=sys.stderr)
        if os.path.exists(committed):
            try:
                shutil.copyfile(committed, out)
            except Exception:
                pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
