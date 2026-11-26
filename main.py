#!/usr/bin/env python3
"""news-image-20261126 — "Sum up 26 November's world news in one image".

A deterministic newspaper renderer: draws one 1024x1024 PNG summarising the
verified world news of Thursday 26 November 2026. Renders internally at
2048x2048 and downscales for sharp text. No network, no randomness, no clock:
two runs produce identical bytes.

Evidence: 27 stories (STORIES), all verified by web search on 26 Nov 2026
to a 01:00 UTC cut-off; event date vs report date recorded per story.
This is an EARLY edition: the day had barely begun at the cut-off, so
Africa has no verified 26 Nov item yet and the panel says so. Confidence is
categorical only: H = corroborated by 2+ independent credible sources,
M = one credible attributed source, developing. No invented percentages.

Layout (1024 px): masthead 10%, 5 illustrated leads 22%, schematic world map
+ UTC timeline 13%, 8-region grid 50%, footer 5%. All counts, map markers
and confidence totals are derived from the STORIES dataset, never typed.
"""

import hashlib
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SCALE = 2
W, H = 1024 * SCALE, 1024 * SCALE

INK = (21, 44, 67)        # #152C43 structure
PAPER = (248, 246, 240)    # #F8F6F0 canvas
STEEL = (52, 101, 138)     # #34658A region accents
GREEN = (36, 118, 83)      # #247653 verified (H)
OCHRE = (138, 109, 27)     # #8A6D1B developing (M), darkened for contrast
LIGHT = (220, 230, 238)    # pale panel
MIDGREY = (110, 118, 126)
RULE = (180, 188, 196)
WHITE = (255, 255, 255)
SCENE_BG = (226, 232, 238)


def _font_path(name):
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", name)
    if os.path.exists(here):
        return here
    return os.path.join("/usr/share/fonts/truetype/dejavu", name)


def font(size, bold=False):
    return ImageFont.truetype(
        _font_path("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        int(size * SCALE),
    )


def wrap(text, fnt, max_w):
    """Greedy wrap by measured width; returns list of lines.

    A single word wider than max_w is hard-split by characters so the
    returned lines always fit; every line is then measured to prove it.
    """
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        if fnt.getlength(w_) > max_w:
            if cur:
                lines.append(cur)
                cur = ""
            piece = ""
            for ch in w_:
                if fnt.getlength(piece + ch) <= max_w:
                    piece += ch
                else:
                    lines.append(piece)
                    piece = ch
            cur = piece
            continue
        trial = (cur + " " + w_).strip()
        if fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    for ln in lines:
        assert fnt.getlength(ln) <= max_w, "LINE TOO WIDE: %r" % ln
    return lines


def draw_wrapped(dr, text, fnt, x, y, max_w, fill, lh, max_lines=None):
    """Draw wrapped text; returns number of lines used."""
    lines = wrap(text, fnt, max_w)
    if max_lines is not None:
        assert len(lines) <= max_lines, "TEXT OVERFLOW: %r -> %d lines" % (text, len(lines))
    for i, ln in enumerate(lines):
        dr.text((x, y + i * lh), ln, font=fnt, fill=fill)
    return len(lines)


# ---------------------------------------------------------------------------
# Frozen evidence dataset (see STORIES.md for sources and dates).
# headline: short grid headline (authored to fit one line at 12px).
# ---------------------------------------------------------------------------
# (id, region, headline, source, conf)
# Headlines are authored to fit one line at 12px in a 328px column.
# Sources are short labels; full names are in the footer + STORIES.md.
STORIES = [
    ("N1", "NA", "Thanksgiving Day across the US", "AP", "H"),
    ("N2", "NA", "Nor'easter drenches East Coast", "WSJ", "H"),
    ("N3", "NA", "US markets shut; futures edge up", "BBG", "M"),
    ("E1", "EU", "EU leaders meet on Ukraine funding", "EurSays", "M"),
    ("E2", "EU", "Poland urges NATO air shield", "DefMatters", "M"),
    ("E3", "EU", "Europe rearmament leans on US kit", "DefMatters", "M"),
    ("A1", "AP", "Asia stocks rebound after US rally", "BBG", "H"),
    ("A2", "AP", "Nikkei +1.3%; chip stocks rally", "WSJ", "H"),
    ("A3", "AP", "India marks Constitution Day", "Observer", "H"),
    ("A4", "AP", "India marks 18 years since 26/11", "Observer", "H"),
    ("A5", "AP", "Kim urges wider tactical nukes", "Reuters", "H"),
    ("A6", "AP", "India, China hold border talks", "Mathrubhumi", "M"),
    ("A7", "AP", "Hasina seeks return to Dhaka", "Mathrubhumi", "M"),
    ("A8", "AP", "India Pavilion wins Venice Lion", "Mathrubhumi", "M"),
    ("A9", "AP", "Modi opens AI centre at IIT Patna", "Studmentor", "M"),
    ("A10", "AP", "SP names five UP poll candidates", "Mathrubhumi", "M"),
    ("A11", "AP", "Ranchi police detain tree protesters", "IndExp", "M"),
    ("M1", "ME", "Gaza truce 'near collapse', board warns", "AJ", "M"),
    ("L1", "LATAM", "Argentina's CGT marches today", "DevEvil", "M"),
    ("L2", "LATAM", "Chile mourns actress Guzman, 98", "DevEvil", "M"),
    ("O1", "OCE", "Fisher & Paykel profit jumps 37%", "NZX", "H"),
    ("O2", "OCE", "Australian shares open higher", "BBG", "M"),
    ("G1", "GL", "Chess title level; Game 3 today", "S.Guardian", "M"),
    ("G2", "GL", "Emirates tops airline rankings", "Studmentor", "M"),
    ("G3", "GL", "Anand Kumar wins award in Japan", "IndExp", "M"),
    ("G4", "GL", "India space economy to hit $45bn", "Studmentor", "M"),
    ("G5", "GL", "Google funds IIT Kharagpur AI", "Studmentor", "M"),
]

# (id, headline, deck, source, scene, conf)
# The wide lead is Thanksgiving (its feast scene fills the wide strip);
# the most important verified international development (Kim's nuclear
# call) is the first small lead, with a contained atom scene.
LEADS = [
    ("N1", "Thanksgiving in America",
     "Storm drenches the East Coast as the US marks the day.",
     "AP", "feast", "H"),
    ("A5", "Kim: widen tactical nuclear use",
     "KCNA reports the call; the visit was Wednesday.",
     "Reuters", "atom", "H"),
    ("A2", "Nikkei rebounds 1.3%",
     "Chip stocks lead Asia higher; Kioxia +11%.",
     "WSJ", "arrow", "H"),
    ("E1", "EU leaders gather on Ukraine funding",
     "Two-day summit to settle Kyiv's 2027 money.",
     "EurSays", "stars", "M"),
    ("O1", "Fisher & Paykel profit jumps 37%",
     "Revenue $1.25bn; guidance and dividend lifted.",
     "NZX", "bars", "H"),
]

# (label, text, story ids) — 26 Nov only; local times labelled.
TIMELINE = [
    ("26 Nov 00:01 UTC", "Asia stocks rebound; Nikkei +1.3%", ("A1", "A2")),
    ("26 Nov, NZ morning", "Fisher & Paykel: profit +37%.", ("O1",)),
    ("26 Nov, early hours", "KCNA reports Kim's nuclear call.", ("A5",)),
    ("26 Nov, morning IST", "India: Constitution Day; 26/11.", ("A3", "A4")),
    ("26 Nov 15:00 CET", "Chess title match, Game 3.", ("G1",)),
    ("26 Nov, daytime", "EU leaders gather on Ukraine.", ("E1",)),
    ("26 Nov, all day", "Thanksgiving Day in the US.", ("N1",)),
]

REGIONS = [
    ("NORTH AMERICA", "NA", ["N1", "N2", "N3"]),
    ("EUROPE", "EU", ["E1", "E2", "E3"]),
    ("ASIA", "AP", ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11"]),
    ("MIDDLE EAST", "ME", ["M1"]),
    ("AFRICA", "AF", []),
    ("LATIN AMERICA", "LATAM", ["L1", "L2"]),
    ("OCEANIA", "OCE", ["O1", "O2"]),
    ("GLOBAL THEMES", "GL", ["G1", "G2", "G3", "G4", "G5"]),
]

LEAD_IDS = {lead[0] for lead in LEADS}

BY_ID = {s[0]: s for s in STORIES}
N_STORIES = len(STORIES)
N_H = sum(1 for s in STORIES if s[4] == "H")
N_M = sum(1 for s in STORIES if s[4] == "M")
assert N_H + N_M == N_STORIES
assert len(BY_ID) == N_STORIES, "duplicate story id"
assert all(len(ids) == len(set(ids)) for _, _, ids in REGIONS)
_flat = [sid for _, _, ids in REGIONS for sid in ids]
assert sorted(_flat) == sorted(BY_ID), "regional ids must match story ids exactly once each"
assert LEAD_IDS <= set(BY_ID), "lead id not in stories"
for _label, _text, _ids in TIMELINE:
    assert all(i in BY_ID for i in _ids), "timeline id not in stories"


# ---------------------------------------------------------------------------
# Symbolic scenes (vector primitives only; labelled as illustrations).
# ---------------------------------------------------------------------------

def scene_feast(dr, x0, y0, x1, y1):
    dr.rectangle([x0, y0, x1, y1], fill=(232, 214, 176))
    dr.ellipse([x0 + 8 * SCALE, y0 + int(0.52 * (y1 - y0)), x1 - 8 * SCALE, y1 - 8 * SCALE],
               fill=(246, 240, 224), outline=INK)
    dr.ellipse([x0 + int(0.30 * (x1 - x0)), y0 + int(0.30 * (y1 - y0)),
                x0 + int(0.70 * (x1 - x0)), y0 + int(0.62 * (y1 - y0))],
               fill=(150, 92, 44))
    dr.ellipse([x0 + int(0.38 * (x1 - x0)), y0 + int(0.22 * (y1 - y0)),
                x0 + int(0.62 * (x1 - x0)), y0 + int(0.44 * (y1 - y0))],
               fill=(176, 112, 58))
    for dx in (-1, 1):
        cx = x0 + int((0.5 + dx * 0.28) * (x1 - x0))
        dr.line([cx, y0 + int(0.42 * (y1 - y0)), cx + dx * 10 * SCALE, y0 + int(0.30 * (y1 - y0))],
                fill=(120, 70, 30), width=3 * SCALE)
        dr.ellipse([cx + dx * 10 * SCALE - 4 * SCALE, y0 + int(0.30 * (y1 - y0)) - 4 * SCALE,
                    cx + dx * 10 * SCALE + 4 * SCALE, y0 + int(0.30 * (y1 - y0)) + 4 * SCALE],
                   fill=(120, 70, 30))
    for i, lx in enumerate((0.16, 0.84)):
        lx = x0 + int(lx * (x1 - x0))
        dr.line([lx, y0 + int(0.72 * (y1 - y0)), lx, y0 + int(0.30 * (y1 - y0))],
                fill=(181, 139, 41), width=2 * SCALE)
        for k in range(3):
            ly = y0 + int((0.34 + k * 0.10) * (y1 - y0))
            dr.ellipse([lx - 5 * SCALE, ly, lx + 5 * SCALE, ly + 5 * SCALE], fill=(201, 154, 52))


def scene_arrow(dr, x0, y0, x1, y1):
    # Symbolic rising arrow only: no plotted price path is invented.
    dr.rectangle([x0, y0, x1, y1], fill=(24, 38, 54))
    w_, h_ = x1 - x0, y1 - y0
    for i in range(1, 4):
        gy = y0 + int(i * h_ / 4)
        dr.line([x0 + 6 * SCALE, gy, x1 - 6 * SCALE, gy], fill=(58, 76, 96), width=SCALE)
    x_start, y_start = x0 + int(0.12 * w_), y0 + int(0.78 * h_)
    x_end, y_end = x0 + int(0.86 * w_), y0 + int(0.22 * h_)
    dr.line([x_start, y_start, x_end, y_end], fill=(74, 160, 110), width=5 * SCALE)
    dr.polygon([(x_end, y_end), (x_end - 16 * SCALE, y_end - 2 * SCALE),
                (x_end - 2 * SCALE, y_end + 16 * SCALE)], fill=(74, 160, 110))
    dr.text((x0 + 8 * SCALE, y0 + 6 * SCALE), "+1.3%", font=font(15, True),
            fill=(140, 210, 170))


def scene_atom(dr, x0, y0, x1, y1):
    # Symbolic atom: nucleus + three orbits. Orbits are sized by the
    # SMALLER scene dimension so they can never escape the box.
    dr.rectangle([x0, y0, x1, y1], fill=(24, 38, 54))
    w_, h_ = x1 - x0, y1 - y0
    cx, cy = x0 + w_ // 2, y0 + h_ // 2
    m = min(w_, h_)
    rx, ry = int(0.38 * m), int(0.15 * m)
    for ang_deg in (0, 60, 120):
        ang = math.radians(ang_deg)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for k in range(49):
            t = 2 * math.pi * k / 48
            ex, ey = rx * math.cos(t), ry * math.sin(t)
            px_ = cx + int(ex * ca - ey * sa)
            py_ = cy + int(ex * sa + ey * ca)
            pts.append((px_, py_))
        dr.line(pts, fill=(120, 160, 190), width=2 * SCALE)
    dr.ellipse([cx - 7 * SCALE, cy - 7 * SCALE, cx + 7 * SCALE, cy + 7 * SCALE],
               fill=(214, 130, 40))
    for ang_deg in (0, 60, 120):
        ang = math.radians(ang_deg)
        ex = cx + int(rx * math.cos(ang))
        ey = cy + int(rx * math.sin(ang))
        dr.ellipse([ex - 4 * SCALE, ey - 4 * SCALE, ex + 4 * SCALE, ey + 4 * SCALE],
                   fill=(140, 210, 170))


def scene_stars(dr, x0, y0, x1, y1):
    # Circle of twelve stars on blue: a summit symbol, no flags of states.
    dr.rectangle([x0, y0, x1, y1], fill=(36, 68, 138))
    w_, h_ = x1 - x0, y1 - y0
    cx, cy = x0 + w_ // 2, y0 + int(0.56 * h_)
    r = int(0.30 * min(w_, h_))
    for k in range(12):
        ang = -math.pi / 2 + k * math.pi / 6
        sx, sy = cx + int(r * math.cos(ang)), cy + int(r * math.sin(ang))
        s = 5 * SCALE
        dr.polygon([(sx, sy - s), (sx + s, sy + s), (sx - s, sy + s)], fill=(246, 214, 90))
        dr.polygon([(sx, sy + s), (sx + s, sy - s), (sx - s, sy - s)], fill=(246, 214, 90))
    dr.text((x0 + 8 * SCALE, y0 + 6 * SCALE), "26-27 NOV", font=font(11, True),
            fill=(255, 255, 255))


def scene_bars(dr, x0, y0, x1, y1):
    # Two independently labelled indicators: revenue +15%, profit +37%.
    # No single gauge mixes two different measures.
    dr.rectangle([x0, y0, x1, y1], fill=(226, 234, 226))
    w_, h_ = x1 - x0, y1 - y0
    data = (("REVENUE", "+15%", 0.45), ("PROFIT", "+37%", 0.82))
    bw = int(0.24 * w_)
    for i, (lab, val, frac) in enumerate(data):
        bx0 = x0 + int((0.10 + i * 0.50) * w_)
        by1 = y1 - 26 * SCALE
        bh = int(frac * (y1 - y0) * 0.45)
        dr.rectangle([bx0, by1 - bh, bx0 + bw, by1], fill=STEEL)
        vf = font(13, True)
        vw = vf.getlength(val)
        dr.text((bx0 + (bw - vw) / 2, by1 - bh - 18 * SCALE), val, font=vf, fill=INK)
        lf = font(8, True)
        lw = lf.getlength(lab)
        dr.text((bx0 + (bw - lw) / 2, by1 + 4 * SCALE), lab, font=lf, fill=(60, 68, 76))


SCENES = {"feast": scene_feast, "arrow": scene_arrow, "atom": scene_atom,
          "stars": scene_stars, "bars": scene_bars}

# ---------------------------------------------------------------------------
# Schematic world map: continent outlines only (lon, lat), no country borders.
# ---------------------------------------------------------------------------
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 73), (-75, 72),
     (-60, 60), (-55, 47), (-65, 45), (-75, 38), (-80, 32), (-90, 30), (-97, 26),
     (-105, 22), (-110, 24), (-117, 33), (-125, 40), (-130, 55), (-150, 60), (-168, 66)],
    [(-55, 60), (-45, 60), (-40, 65), (-30, 68), (-22, 70), (-25, 76), (-35, 80),
     (-50, 80), (-58, 76), (-60, 70), (-55, 60)],
    [(-80, 10), (-75, 7), (-60, 5), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
     (-55, -35), (-65, -45), (-70, -55), (-73, -40), (-73, -25), (-80, -15), (-80, 10)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59), (18, 56),
     (21, 55), (24, 59), (30, 60), (30, 70), (20, 70), (12, 70), (5, 62), (5, 58),
     (-5, 50), (-10, 36)],
    [(-6, 35), (0, 36), (10, 37), (20, 32), (32, 31), (35, 28), (40, 22), (43, 12),
     (48, 11), (51, 10), (44, 0), (40, -10), (35, -20), (32, -28), (28, -33),
     (20, -35), (15, -30), (12, -18), (8, -2), (9, 4), (-8, 5), (-15, 12),
     (-17, 20), (-16, 28), (-10, 31), (-6, 35)],
    [(30, 70), (40, 68), (55, 69), (70, 72), (90, 75), (110, 76), (130, 72),
     (160, 70), (178, 66), (170, 60), (162, 56), (158, 50), (142, 45), (140, 40),
     (135, 35), (130, 32), (127, 35), (122, 30), (120, 25), (115, 22), (108, 18),
     (105, 10), (100, 8), (97, 15), (92, 21), (88, 22), (80, 15), (76, 8),
     (72, 20), (66, 25), (60, 25), (55, 26), (50, 29), (48, 30), (43, 28),
     (40, 35), (36, 36), (30, 36), (30, 42), (28, 45), (30, 60), (30, 70)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32), (135, -35),
     (140, -38), (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -15), (132, -11),
     (130, -13), (126, -14), (122, -17), (118, -20), (113, -22)],
    [(166, -34), (170, -37), (174, -39), (178, -38), (176, -35), (172, -34), (166, -34)],
]

# (number, label, lon, lat, side) — counts are derived from REGIONS below,
# never typed. Asia and Oceania are separate markers.
_MARKER_POS = [
    (1, "N. America", "NA", -100, 48, "r"),
    (2, "Europe", "EU", 12, 52, "r"),
    (3, "Asia", "AP", 105, 28, "b"),
    (4, "Middle East", "ME", 44, 26, "l"),
    (5, "Africa", "AF", 18, 4, "r"),
    (6, "Latin America", "LATAM", -60, -14, "r"),
    (7, "Oceania", "OCE", 134, -25, "r"),
]
_COUNTS = {code: len(ids) for _, code, ids in REGIONS}
MARKERS = [(num, label, lon, lat, _COUNTS[code], side)
           for num, label, code, lon, lat, side in _MARKER_POS]
GLOBAL_COUNT = _COUNTS["GL"]


def draw_map(dr, x0, y0, x1, y1):
    dr.rectangle([x0, y0, x1, y1], fill=(233, 240, 246), outline=RULE, width=SCALE)
    mw, mh = x1 - x0, y1 - y0

    def px(lon, lat):
        # Latitudes run to 80 (Greenland); the old 75 deg cap pushed the
        # coastline over the box top. Range is now 85 to -60.
        return (x0 + int((lon + 180) / 360 * mw),
                y0 + int((85 - lat) / 145 * mh))

    for poly in CONTINENTS:
        dr.polygon([px(lo, la) for lo, la in poly], fill=(206, 220, 232), outline=STEEL)
    dr.text((x0 + 6 * SCALE, y0 + 4 * SCALE), "WHERE THE NEWS FELL — STORIES BY REGION",
            font=font(11, True), fill=STEEL)
    for num, label, lon, lat, count, side in MARKERS:
        cx, cy = px(lon, lat)
        r = 10 * SCALE
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK, outline=WHITE, width=2 * SCALE)
        t = str(num)
        tw = dr.textlength(t, font=font(11, True))
        dr.text((cx - tw / 2, cy - 7 * SCALE), t, font=font(11, True), fill=WHITE)
        tag = "%s %d" % (label, count)
        tf = font(10, True)
        tw = tf.getlength(tag)
        if side == "l":
            tx = cx - r - 3 * SCALE - tw
            ty = cy - 7 * SCALE
        elif side == "b":
            tx = cx - tw / 2
            ty = cy + r + 3 * SCALE
        else:
            tx = cx + r + 3 * SCALE
            ty = cy - 7 * SCALE
        tx = min(max(tx, x0 + 4 * SCALE), x1 - tw - 4 * SCALE)
        ty = min(max(ty, y0 + 16 * SCALE), y1 - 14 * SCALE)
        dr.rectangle([tx - 3 * SCALE, ty - 2 * SCALE, tx + tw + 3 * SCALE, ty + 12 * SCALE],
                     fill=WHITE, outline=STEEL, width=SCALE)
        dr.text((tx, ty), tag, font=tf, fill=INK)
    chip = "GLOBAL THEMES %d" % GLOBAL_COUNT
    cf = font(10, True)
    cw = cf.getlength(chip)
    dr.rectangle([x1 - cw - 12 * SCALE, y1 - 18 * SCALE, x1 - 4 * SCALE, y1 - 4 * SCALE],
                 fill=WHITE, outline=STEEL, width=SCALE)
    dr.text((x1 - cw - 9 * SCALE, y1 - 16 * SCALE), chip, font=cf, fill=INK)
    dr.text((x0 + 6 * SCALE, y1 - 15 * SCALE), "Schematic — shapes simplified, not to scale.",
            font=font(9), fill=MIDGREY)


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def draw_masthead(dr):
    dr.rectangle([0, 0, W, 92 * SCALE], fill=PAPER)
    dr.text((12 * SCALE, 10 * SCALE), "THE WORLD IN ONE DAY", font=font(34, True), fill=INK)
    dr.text((12 * SCALE, 52 * SCALE),
            "Events of 26 Nov 2026 in local time, or within 26 Nov UTC.",
            font=font(12), fill=MIDGREY)
    dr.text((12 * SCALE, 70 * SCALE), "THURSDAY 26 NOVEMBER 2026  ·  EARLY EDITION",
            font=font(19, True), fill=STEEL)
    right = "%d STORIES  ·  8 REGIONS" % N_STORIES
    rf = font(22, True)
    dr.text((W - 12 * SCALE - rf.getlength(right), 14 * SCALE), right, font=rf, fill=INK)
    sub = "%d confirmed  ·  %d developing  ·  cut-off 01:00 UTC" % (N_H, N_M)
    sf = font(12)
    dr.text((W - 12 * SCALE - sf.getlength(sub), 48 * SCALE), sub, font=sf, fill=MIDGREY)
    dr.line([0, 92 * SCALE, W, 92 * SCALE], fill=INK, width=3 * SCALE)


def draw_lead_card(dr, img, x0, y0, x1, y1, lead, wide):
    sid, headline, deck, source, scene, conf = lead
    dr.rectangle([x0, y0, x1, y1], fill=WHITE, outline=RULE, width=SCALE)
    meta = "%s  ·  %s  ·  %s" % (sid, source, conf)

    def paste_scene(x0s, y0s, x1s, y1s):
        # Render the scene on its own layer and paste it: nothing the
        # scene draws can escape its box (clipped at the layer edge).
        w_, h_ = x1s - x0s, y1s - y0s
        tmp = Image.new("RGB", (w_, h_))
        tdr = ImageDraw.Draw(tmp)
        SCENES[scene](tdr, 0, 0, w_, h_)
        img.paste(tmp, (x0s, y0s))

    if wide:
        sx0, sy0, sx1, sy1 = x0, y0, x1, y0 + 100 * SCALE
        paste_scene(sx0, sy0, sx1, sy1)
        lab = "SYMBOLIC ILLUSTRATION"
        lf = font(9, True)
        lw = lf.getlength(lab)
        dr.rectangle([sx0 + 6 * SCALE, sy1 - 18 * SCALE,
                      sx0 + 6 * SCALE + lw + 8 * SCALE, sy1 - 4 * SCALE], fill=INK)
        dr.text((sx0 + 10 * SCALE, sy1 - 16 * SCALE), lab, font=lf, fill=WHITE)
        tx, ty = x0 + 10 * SCALE, y0 + 108 * SCALE
        tw = x1 - x0 - 20 * SCALE
        n = draw_wrapped(dr, headline, font(17, True), tx, ty, tw, INK, 21 * SCALE, max_lines=2)
        ty += n * 21 * SCALE + 4 * SCALE
        n = draw_wrapped(dr, deck, font(12), tx, ty, tw, (60, 68, 76), 15 * SCALE, max_lines=2)
        ty += n * 15 * SCALE + 4 * SCALE
        dr.text((tx, ty), meta, font=font(10, True), fill=STEEL)
        assert ty + 14 * SCALE <= y1, "LEAD CARD OVERFLOW: %s" % sid
    else:
        sw = 92 * SCALE
        paste_scene(x0, y0, x0 + sw, y1)
        lab = "SYMBOLIC"
        lf = font(8, True)
        lw = lf.getlength(lab)
        dr.rectangle([x0 + 4 * SCALE, y1 - 15 * SCALE,
                      x0 + 4 * SCALE + lw + 6 * SCALE, y1 - 3 * SCALE], fill=INK)
        dr.text((x0 + 7 * SCALE, y1 - 13 * SCALE), lab, font=lf, fill=WHITE)
        tx, ty = x0 + sw + 8 * SCALE, y0 + 6 * SCALE
        tw = x1 - tx - 8 * SCALE
        n = draw_wrapped(dr, headline, font(15, True), tx, ty, tw, INK, 18 * SCALE, max_lines=2)
        ty += n * 18 * SCALE + 3 * SCALE
        n = draw_wrapped(dr, deck, font(11), tx, ty, tw, (60, 68, 76), 14 * SCALE, max_lines=2)
        ty += n * 14 * SCALE + 3 * SCALE
        dr.text((tx, ty), meta, font=font(10, True), fill=STEEL)
        assert ty + 14 * SCALE <= y1, "LEAD CARD OVERFLOW: %s" % sid


def draw_leads(dr, img):
    draw_lead_card(dr, img, 12 * SCALE, 100 * SCALE, 412 * SCALE, 292 * SCALE, LEADS[0], wide=True)
    cells = [
        (420 * SCALE, 100 * SCALE, 712 * SCALE, 192 * SCALE, LEADS[1]),
        (720 * SCALE, 100 * SCALE, 1012 * SCALE, 192 * SCALE, LEADS[2]),
        (420 * SCALE, 200 * SCALE, 712 * SCALE, 292 * SCALE, LEADS[3]),
        (720 * SCALE, 200 * SCALE, 1012 * SCALE, 292 * SCALE, LEADS[4]),
    ]
    for x0, y0, x1, y1, lead in cells:
        draw_lead_card(dr, img, x0, y0, x1, y1, lead, wide=False)
    dr.line([0, 300 * SCALE, W, 300 * SCALE], fill=RULE, width=SCALE)


def draw_timeline(dr, x0, y0, x1, y1):
    dr.text((x0, y0 + 2 * SCALE), "THE DAY — WHEN THE NEWS BROKE",
            font=font(12, True), fill=STEEL)
    tf, bf = font(9), font(10, True)
    y = y0 + 18 * SCALE
    for label, text, ids in TIMELINE:
        full = "%s (%s)" % (text, ", ".join(ids))
        dr.text((x0, y), label, font=bf, fill=INK)
        lines = wrap(full, tf, (x1 - x0) - bf.getlength(label) - 8 * SCALE)
        assert len(lines) == 1, "TIMELINE OVERFLOW: %r" % full
        dr.text((x0 + bf.getlength(label) + 8 * SCALE, y), lines[0], font=tf,
                fill=(60, 68, 76))
        y += 14 * SCALE
    note = "Local times labelled; cut-off 01:00 UTC."
    dr.text((x0, y + 1 * SCALE), note, font=font(9), fill=MIDGREY)
    assert y + 13 * SCALE <= y1, "TIMELINE OVERFLOW: note past box"


def draw_grid(dr):
    col_x = [12 * SCALE, 348 * SCALE, 684 * SCALE]
    col_w = 328 * SCALE
    order = [REGIONS[0], REGIONS[1], REGIONS[2],
             REGIONS[3], REGIONS[4], REGIONS[5],
             REGIONS[6], REGIONS[7], None]
    hf, sf, mf = font(15, True), font(12), font(10, True)
    grid_top, grid_bottom = 452 * SCALE, 968 * SCALE
    gap = 8 * SCALE

    def panel_need(reg):
        # Header + lead line (if any) + one row per non-lead story + padding.
        if reg is None:
            return 120 * SCALE
        _, _, ids = reg
        n_listed = len([i for i in ids if i not in LEAD_IDS])
        need = 24 * SCALE + 8 * SCALE
        if any(i in LEAD_IDS for i in ids):
            need += 15 * SCALE
        if ids:
            need += n_listed * 17 * SCALE
        else:
            need += 2 * 15 * SCALE  # honest empty-panel note
        return need

    row_need = [max(panel_need(order[r * 3 + c]) for c in range(3)) for r in range(3)]
    total_need = sum(row_need) + 2 * gap
    slack = (grid_bottom - grid_top) - total_need
    assert slack >= 0, "GRID TOO TALL: need %d, have %d" % (total_need, grid_bottom - grid_top)
    row_h = [h + slack // 3 for h in row_need]
    rows = []
    y = grid_top
    for h in row_h:
        rows.append((y, h))
        y += h + gap

    for idx, reg in enumerate(order):
        cx = col_x[idx % 3]
        cy, ch = rows[idx // 3]
        if reg is None:
            # How-to-read box fills the ninth cell (compact, not a legend panel).
            dr.rectangle([cx, cy, cx + col_w, cy + ch], fill=LIGHT, outline=RULE, width=SCALE)
            tx, ty = cx + 8 * SCALE, cy + 8 * SCALE
            dr.text((tx, ty), "HOW TO READ THIS PAGE", font=hf, fill=INK)
            ty += 22 * SCALE
            notes = [
                "H  verified by 2+ independent sources",
                "M  one attributed source, developing",
                "IDs link stories across timeline and regions.",
                "Leads (starred) are shown in full at the top;",
                "they are counted once, not twice.",
                "Scenes are symbolic drawings, not photos.",
            ]
            for nt in notes:
                lines = wrap(nt, font(11), col_w - 16 * SCALE)
                for ln in lines:
                    dr.text((tx, ty), ln, font=font(11), fill=(60, 68, 76))
                    ty += 15 * SCALE
            assert ty <= cy + ch - 4 * SCALE, "HOW-TO OVERFLOW"
            continue
        name, code, ids = reg
        dr.rectangle([cx, cy, cx + col_w, cy + ch], fill=WHITE, outline=RULE, width=SCALE)
        dr.rectangle([cx, cy, cx + col_w, cy + 24 * SCALE], fill=STEEL)
        dr.text((cx + 8 * SCALE, cy + 4 * SCALE),
                "%s  ·  %d" % (name, len(ids)), font=font(13, True), fill=WHITE)
        tx = cx + 8 * SCALE
        ty = cy + 30 * SCALE
        lead_refs = [i for i in ids if i in LEAD_IDS]
        if lead_refs:
            dr.text((tx, ty), "★ Leads above: " + " · ".join(lead_refs),
                    font=font(11, True), fill=STEEL)
            ty += 15 * SCALE
        if not ids:
            lines = wrap("No verified 26 Nov item by the 01:00 UTC cut-off.",
                         font(11), col_w - 16 * SCALE)
            for ln in lines:
                dr.text((tx, ty), ln, font=font(11), fill=(60, 68, 76))
                ty += 15 * SCALE
        for sid in ids:
            if sid in LEAD_IDS:
                continue
            _, _, headline, source, conf = BY_ID[sid]
            dot = GREEN if conf == "H" else OCHRE
            dr.ellipse([tx, ty + 4 * SCALE, tx + 7 * SCALE, ty + 11 * SCALE], fill=dot)
            meta = "%s %s" % (source, conf)
            mw = mf.getlength(meta)
            lines = wrap(headline, sf, col_w - 24 * SCALE - mw - 6 * SCALE)
            assert len(lines) == 1, "GRID OVERFLOW: %s %r" % (sid, headline)
            dr.text((tx + 12 * SCALE, ty), lines[0], font=sf, fill=INK)
            dr.text((cx + col_w - 8 * SCALE - mw, ty + 1 * SCALE), meta, font=mf,
                    fill=GREEN if conf == "H" else OCHRE)
            ty += 17 * SCALE
        assert ty <= cy + ch - 4 * SCALE, "GRID PANEL OVERFLOW: %s" % name


def draw_footer(dr):
    dr.line([0, 968 * SCALE, W, 968 * SCALE], fill=INK, width=2 * SCALE)
    lines = [
        ("Sources: AP · Reuters · CNN · Bloomberg · WSJ · USA Today · "
         "Straits Times · Korea Times · NZX · The Press · Al Jazeera", 10),
        ("Mathrubhumi · Indian Express · Observer Voice · Jagran Josh · "
         "Defence Matters · EuropeSays · Sunday Guardian · Nettsak · "
         "Studmentor · SelfStudys · DevEvil News", 10),
        ("H = verified by 2+ independent sources  ·  M = one attributed source, "
         "developing  ·  Early edition — cut-off 01:00 UTC 26 Nov 2026  ·  "
         "Scenes are symbolic, not photographs.", 10),
    ]
    y = 974 * SCALE
    for text, size in lines:
        fnt = font(size)
        assert fnt.getlength(text) <= W - 24 * SCALE, "FOOTER OVERFLOW: %r" % text
        dr.text((12 * SCALE, y), text, font=fnt, fill=(60, 68, 76))
        y += 16 * SCALE


def render():
    img = Image.new("RGB", (W, H), PAPER)
    dr = ImageDraw.Draw(img)
    draw_masthead(dr)
    draw_leads(dr, img)
    draw_map(dr, 12 * SCALE, 308 * SCALE, 660 * SCALE, 444 * SCALE)
    draw_timeline(dr, 672 * SCALE, 308 * SCALE, 1012 * SCALE, 444 * SCALE)
    draw_grid(dr)
    draw_footer(dr)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = render()
    small = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    path = os.path.join(out_dir, "entry.png")
    small.save(path, "PNG", optimize=True, compress_level=9)
    if os.path.getsize(path) > 1048576:
        # Deterministic lossless fallback: re-save at max compression.
        small.save(path, "PNG", optimize=True, compress_level=9)
    # Validate the SAVED file by reopening it, not just the in-memory image.
    with Image.open(path) as check:
        check.load()
        assert check.size == (1024, 1024), "saved size %r" % (check.size,)
        assert check.mode == "RGB", "saved mode %r" % check.mode
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    print("wrote %s (%d bytes, sha256 %s)" % (path, size, digest))
    assert size <= 1048576, "entry.png over 1 MiB: %d" % size
    return 0


if __name__ == "__main__":
    sys.exit(main())
