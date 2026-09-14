"""
build_artwork.py -- generates every master artwork SVG for the
SuperteamTR T-Shirt project.

Outputs
-------
design/concepts/  concept-1-futuristic-arena.svg      (hero direction)
                  concept-2-blueprint-network.svg     (technical direction)
                  concept-3-premium-minimal-seal.svg  (minimal direction)
design/final/     final-back-print-on-dark.svg        (320 x 400 mm, 4 inks + gradient)
                  final-back-print-on-light.svg       (320 x 400 mm, dark-ink variant)
                  final-front-chest.svg               (84 x 96 mm)
                  final-front-chest-on-light.svg
                  final-neck-label.svg                (inside-neck detail)
                  final-sleeve-mark.svg               (optional sleeve hit)

Run:  python3 tools/build_artwork.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import pathparse
from lib import svgutil as su
from lib.inks import INK, GRADIENT_PRINT_MAP  # noqa: F401  (re-exported for tools)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "brand-assets", "official")
FONTS = os.path.join(ROOT, "fonts")

WHITE = INK["WHITE"]["hex"]
RED = INK["TR_RED"]["hex"]
PURPLE = INK["SOLANA_PURPLE"]["hex"]
GREEN = INK["SOLANA_GREEN"]["hex"]
TEAL = INK["SOLANA_TEAL"]["hex"]
INK_BLACK = INK["BLUEPRINT_BLACK"]["hex"]

# --------------------------------------------------------------------------- #
#  shared setup
# --------------------------------------------------------------------------- #

_logos: dict[str, su.LogoAsset] = {}


def logo(name: str) -> su.LogoAsset:
    if name not in _logos:
        _logos[name] = su.load_logo(os.path.join(ASSETS, name))
    return _logos[name]


SHAPERS: dict[str, su.Shaper] = {}


def shaper(name: str) -> su.Shaper:
    if name not in SHAPERS:
        if name == "display":
            SHAPERS[name] = su.Shaper(os.path.join(FONTS, "Anton-Regular.ttf"), cache_key="anton")
        elif name == "grotesk-700":
            SHAPERS[name] = su.Shaper(os.path.join(FONTS, "SpaceGrotesk-VF.ttf"), weight=700)
        elif name == "grotesk-500":
            SHAPERS[name] = su.Shaper(os.path.join(FONTS, "SpaceGrotesk-VF.ttf"), weight=500)
        elif name == "mono-500":
            SHAPERS[name] = su.Shaper(os.path.join(FONTS, "JetBrainsMono-VF.ttf"), weight=500)
        elif name == "mono-400":
            SHAPERS[name] = su.Shaper(os.path.join(FONTS, "JetBrainsMono-VF.ttf"), weight=400)
        else:
            raise KeyError(name)
    return SHAPERS[name]


class Ink:
    """Ink role -> colour, swappable for light-garment variants."""

    def __init__(self, base: str = WHITE, red: str = RED):
        self.base = base
        self.red = red
        self.purple = PURPLE
        self.green = GREEN
        self.teal = TEAL


# --------------------------------------------------------------------------- #
#  primitives (all filled paths)
# --------------------------------------------------------------------------- #


def bar(doc: su.Doc, ink: str, x0, y0, x1, y1, w):
    doc.path(su.bar_d(x0, y0, x1, y1, w), ink)


def dot(doc: su.Doc, ink: str, cx, cy, r):
    doc.path(su.dot_d(cx, cy, r), ink)


def ring(doc: su.Doc, ink: str, cx, cy, r_out, r_in):
    doc.path(su.ring_d(cx, cy, r_out, r_in), ink)


def radial_tick(doc, ink, cx, cy, ang, r0, r1, w):
    p0 = su._polar(cx, cy, r0, ang)
    p1 = su._polar(cx, cy, r1, ang)
    bar(doc, ink, p0[0], p0[1], p1[0], p1[1], w)


def arch(doc, ink, cx, cy, ang, r_base, w, h, t):
    """Arcade portal: squared base on the r_base circle, semicircular top outward."""
    pl = su.Place(*su._polar(cx, cy, r_base, ang), rot=ang)
    d = su._arch_local(w, h, t, 0.0)
    doc.path(_apply(d, pl), ink)


def _apply(d: str, pl: su.Place) -> str:
    """Bake a Place transform into absolute path data (keeps exported files simple)."""
    a = math.radians(pl.rot)
    ca, sa = math.cos(a) * pl.scale, math.sin(a) * pl.scale
    return pathparse.transform_d(d, (ca, sa, -sa, ca, pl.x, pl.y))


def text_path(doc, ink, text, *, font, size, x, y, tracking=0.0, anchor="start"):
    d, w = shaper(font).path(text, size, x=x, baseline=y, tracking=tracking, anchor=anchor)
    if d:
        doc.path(d, ink)
    return w


def fit_size(font: str, text: str, target_width: float, tracking_em: float) -> float:
    """Binary-search a font size so tracked text lands on target_width (mm)."""
    lo, hi = 0.5, 400.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        w = shaper(font).measure(text, mid, tracking=tracking_em * mid)
        if w < target_width:
            lo = mid
        else:
            hi = mid
    return lo


def micro(doc, ink, text, *, x, y, size=4.6, tracking_em=0.34, font="mono-500", anchor="start"):
    return text_path(doc, ink, text.upper(), font=font, size=size, x=x, y=y,
                     tracking=tracking_em * size, anchor=anchor)


# --------------------------------------------------------------------------- #
#  the emblem:  "ARENA PROTOCOL"
# --------------------------------------------------------------------------- #


def arena_emblem(
    doc: su.Doc,
    *,
    cx: float,
    cy: float,
    R: float,
    ink: Ink,
    detail: str = "full",
    node_count: int = 12,
    arch_count: int = 24,
    arch2_count: int = 16,
    tick_count: int = 72,
    player_angle: float = 128.0,
    telemetry: bool = True,
) -> None:
    """Draw the circular 'futuristic Colosseum' arena -- the heart of the design.

    Layer order (back to front):
      1  East-West axis ('the bridge') -- dashed, passes behind the arena wall
      2  main arcade band (24 arched openings) + second tier (16 openings)
      3  arena floor: seating spokes, floor ring, gate rail, player marker
      4  core coin: white disc + official Solana logomark (unmodified asset)
      5  Solana network node ring (dashed signal circle + 12 nodes)
      6  telemetry tick ring
      7  gate keystones (4 in SuperteamTR red)
      8  outer frame ring with two 'glitch' breaks and red index squares
      9  technical read-outs (left index / right data bars)
    """
    B, Rr = ink.base, ink.red
    full = detail == "full"

    # 1 -- East-West axis bridge ------------------------------------------------- #
    dash, gap = R * 0.020, R * 0.014
    x = cx - R * 0.93
    while x < cx + R * 0.93:
        x1 = min(x + dash, cx + R * 0.93)
        bar(doc, B, x, cy, x1, cy, R * 0.0068)
        x = x1 + gap
    for s_ in (-1, 1):
        bar(doc, B, cx + s_ * R * 0.885, cy - R * 0.030, cx + s_ * R * 0.885, cy + R * 0.030, R * 0.008)
        bar(doc, B, cx + s_ * R * 0.40, cy - R * 0.026, cx + s_ * R * 0.40, cy + R * 0.026, R * 0.008)

    # 2 -- arcades ------------------------------------------------------------- #
    def arcade(r_in, r_out, count, open_ratio, crown_ratio, skip, tol):
        band = r_out - r_in
        pitch = (2 * math.pi * (r_in + r_out) / 2.0) / count
        hole_w = pitch * open_ratio
        hole_h = band * crown_ratio
        doc.path(su.arcade_band_d(cx, cy, r_in, r_out, count, hole_w, hole_h,
                                  skip=skip, skip_tol=tol), B)

    arcade(R * 0.615, R * 0.775, arch_count, 0.58, 0.62, (0.0, 270.0), 3.0)
    arcade(R * 0.468, R * 0.588, arch2_count, 0.58, 0.62, (90.0, 270.0), 3.0)

    # 3 -- arena floor ---------------------------------------------------------- #
    ring(doc, B, cx, cy, R * 0.330, R * 0.322)
    ring(doc, B, cx, cy, R * 0.212, R * 0.206)
    for i in range(16):
        a = i * 360.0 / 16
        radial_tick(doc, B, cx, cy, a, R * 0.238, R * 0.305, R * 0.0040)
    for q in range(4):
        a = 45 + q * 90
        px, py = su._polar(cx, cy, R * 0.268, a)
        bar(doc, B, px - R * 0.018, py, px + R * 0.018, py, R * 0.0062)
        bar(doc, B, px, py - R * 0.018, px, py + R * 0.018, R * 0.0062)
    px, py = su._polar(cx, cy, R * 0.268, player_angle)
    dot(doc, Rr, px, py, R * 0.0125)

    # 4 -- core coin + official Solana logomark --------------------------------- #
    doc.path(su.circle_d(cx, cy, R * 0.172), B)
    doc.path(su.ring_d(cx, cy, R * 0.181, R * 0.176), Rr)
    su.place_logo(doc, logo("solanaLogoMark.svg"),
                  x=cx, y=cy - (R * 0.30) * (88.0 / 101.0) / 2.0,
                  width=R * 0.30, align="center")

    # 5 -- Solana network node ring (dashed signal circle + nodes) --------------- #
    r_node = R * 0.875
    for i in range(36):
        a0 = i * 10.0
        doc.path(su.arc_band_d(cx, cy, R * 0.8265, R * 0.8225, a0, a0 + 5.6), B)
    seg, seg_gap = 9.0, 5.0
    n_seg = int(360 / (seg + seg_gap))
    for i in range(n_seg):
        a0 = i * (seg + seg_gap)
        doc.path(su.arc_band_d(cx, cy, r_node + R * 0.0035, r_node - R * 0.0035, a0, a0 + seg), B)
    for i in range(node_count):
        a = i * 360.0 / node_count
        radial_tick(doc, B, cx, cy, a, r_node, R * 0.912, R * 0.0038)
        nx, ny = su._polar(cx, cy, r_node, a)
        dot(doc, B, nx, ny, R * 0.0125)
        doc.path(su.ring_d(nx, ny, R * 0.029, R * 0.0255), B)

    # 6 -- telemetry tick ring -------------------------------------------------- #
    if full:
        for i in range(tick_count):
            a = i * 360.0 / tick_count
            d45 = min((a % 45), 45 - (a % 45))
            if d45 < 4.0:
                continue
            long_tick = (i % 6 == 0)
            radial_tick(doc, B, cx, cy, a, R * (0.943 if long_tick else 0.951), R * 0.975,
                        R * (0.0042 if long_tick else 0.0034))

    # 7 -- gate keystones ------------------------------------------------------- #
    for i in range(8):
        a = i * 45.0
        c = Rr if i % 2 == 0 else B
        radial_tick(doc, c, cx, cy, a, R * 0.912, R * 0.943, R * 0.0105)
        px, py = su._polar(cx, cy, R * 0.9275, a)

    # 8 -- outer frame ring with glitch breaks ---------------------------------- #
    for a0, a1 in ((24.0, 201.0), (204.0, 381.0)):
        doc.path(su.arc_band_d(cx, cy, R, R * 0.9885, a0 - 6.0, a1 + 6.0), B)
    for a in (22.5, 202.5):
        px, py = su._polar(cx, cy, R * 0.9943, a)
        doc.path(_apply(su.rect_d(-R * 0.011, -R * 0.011, R * 0.022, R * 0.022),
                        su.Place(px, py, rot=a + 45)), Rr)
    for a in (112.5, 292.5):
        px, py = su._polar(cx, cy, R * 0.9943, a)
        doc.path(_apply(su.rect_d(-R * 0.010, -R * 0.010, R * 0.020, R * 0.020),
                        su.Place(px, py, rot=a + 45)), B)

    # 9 -- technical read-outs -------------------------------------------------- #
    if telemetry:
        for i, L in enumerate((0.20, 0.115, 0.235, 0.075, 0.165)):
            y = cy - R * 0.16 + i * R * 0.075
            bar(doc, B, cx + R * 1.045, y, cx + R * (1.045 + L), y, R * 0.0075)
        doc.path(su.rect_d(cx + R * 1.045, cy + R * 0.22, R * 0.032, R * 0.032), Rr)
        doc.path(su.rect_d(cx - R * 1.077 - R * 0.032, cy - R * 0.32, R * 0.032, R * 0.032), Rr)
        bar(doc, B, cx - R * 1.077 - R * 0.165, cy - R * 0.185, cx - R * 1.077, cy - R * 0.185, R * 0.0075)
        bar(doc, B, cx - R * 1.077 - R * 0.11, cy - R * 0.11, cx - R * 1.077, cy - R * 0.11, R * 0.0075)


# --------------------------------------------------------------------------- #
#  FINAL ARTWORK -- back print
# --------------------------------------------------------------------------- #


def build_back_print(dark: bool, detail: str = "full", *,
                     gradient: str = "full", one_color: bool = False,
                     two_color: bool = False) -> str:
    W, H = 320.0, 400.0
    doc = su.Doc(W, H)
    ink = Ink(base=WHITE if dark else INK_BLACK)
    base = ink.base
    if one_color:
        doc.color_map = {RED.lower(): base, PURPLE.lower(): base,
                         GREEN.lower(): base, TEAL.lower(): base}
        doc.gradient_mode, doc.gradient_colors = "flat", (base,)
    elif two_color:
        doc.color_map = {RED.lower(): base}
        doc.gradient_mode, doc.gradient_colors = "flat", (GREEN,)
    elif gradient == "print":
        doc.gradient_mode, doc.gradient_colors = "hard2", (PURPLE, TEAL)

    # ---- top micro data row
    micro(doc, base, "Istanbul \u00b7 TR", x=26, y=20, size=4.7, tracking_em=0.34)
    micro(doc, base, "41.0082\u00b0 N / 28.9784\u00b0 E", x=294, y=20,
          size=4.7, tracking_em=0.34, anchor="end")

    # ---- arena
    arena_emblem(doc, cx=160.0, cy=152.0, R=112.0, ink=ink)

    # ---- divider rule with index marks
    bar(doc, base, 26, 268, 294, 268, 0.55)
    for x in (26, 160, 294):
        bar(doc, base, x, 264.6, x, 271.4, 1.5)
    bar(doc, ink.red, 26, 268, 62, 268, 1.5)   # red accent: 'TR' index segment

    # ---- official SuperteamTR lockup (unmodified asset, recoloured for print)
    su.place_logo(doc, logo("superteamtr-lockup-horizontal.svg"),
                  x=160.0, y=280.0, width=202.0, align="center",
                  recolor=base)

    # ---- tagline
    tagline = "THE ARENA FOR BUILDERS"
    size = fit_size("display", tagline, 248.0, 0.09)
    text_path(doc, base, tagline, font="display", size=size, x=160.0, y=364.0,
              tracking=0.09 * size, anchor="middle")

    # ---- official Solana logotype (mark + wordmark, unmodified asset)
    su.place_logo(doc, logo("solanaLogo.svg"), x=160.0, y=370.0, width=82.0, align="center")

    # ---- bottom micro line
    micro(doc, base, "Connect. Create. Ship.", x=160, y=391.5,
          size=4.2, tracking_em=0.42, anchor="middle")

    note = ("WHITE base ink #FFFFFF  |  TR_RED #D6223B  |  "
            "SOLANA_PURPLE #9945FF  |  SOLANA_TEAL #28E0B9  |  "
            "Solana logomark gradient #9945FF -> #14F195 (print build: flat / hard-stop)")
    return stamp(doc, note)


# --------------------------------------------------------------------------- #
#  FINAL ARTWORK -- front chest, sleeve, neck
# --------------------------------------------------------------------------- #


def build_front_chest(dark: bool, *, gradient: str = "full",
                      one_color: bool = False, two_color: bool = False) -> str:
    W, H = 90.0, 104.0
    doc = su.Doc(W, H)
    ink = Ink(base=WHITE if dark else INK_BLACK)
    base = ink.base
    if one_color:
        doc.color_map = {RED.lower(): base, PURPLE.lower(): base,
                         GREEN.lower(): base, TEAL.lower(): base}
        doc.gradient_mode, doc.gradient_colors = "flat", (base,)
    elif two_color:
        doc.color_map = {RED.lower(): base}
        doc.gradient_mode, doc.gradient_colors = "flat", (GREEN,)
    elif gradient == "print":
        doc.gradient_mode, doc.gradient_colors = "hard2", (PURPLE, TEAL)
    arena_emblem(doc, cx=45.0, cy=46.0, R=29.5, ink=ink,
                 node_count=8, arch_count=16, tick_count=0, telemetry=False,
                 player_angle=200.0)
    micro(doc, base, "SuperteamTR", x=45.0, y=88.0, size=5.6, tracking_em=0.40,
          anchor="middle")
    micro(doc, base, "Solana Ecosystem", x=45.0, y=97.0, size=3.6, tracking_em=0.34,
          anchor="middle")
    return stamp(doc, "WHITE #FFFFFF | TR_RED #D6223B | Solana gradient "
                      "#9945FF -> #14F195 (print build: flat)")


def build_sleeve_mark(dark: bool, *, one_color: bool = False) -> str:
    W, H = 44.0, 44.0
    doc = su.Doc(W, H)
    ink = Ink(base=WHITE if dark else INK_BLACK)
    base = ink.base
    if one_color:
        doc.color_map = {RED.lower(): base, PURPLE.lower(): base,
                         GREEN.lower(): base, TEAL.lower(): base}
        doc.gradient_mode, doc.gradient_colors = "flat", (base,)
    ring(doc, base, 22, 22, 21.0, 20.1)
    for i in range(12):
        arch(doc, base, 22, 22, i * 30.0, 12.4, 4.6, 5.4, 0.55)
    # central portal with the official Solana logomark
    doc.path(_apply(su._arch_local(7.4, 9.6, 0.0, 0.0), su.Place(22.0, 22.0)), base)
    su.place_logo(doc, logo("solanaLogoMark.svg"), x=22.0, y=15.2, width=5.4, align="center")
    micro(doc, base, "SUPERTEAMTR", x=22.0, y=39.5, size=2.7, tracking_em=0.30, anchor="middle")
    return stamp(doc, "WHITE #FFFFFF | Solana gradient #9945FF -> #14F195")


def build_neck_label(dark: bool, *, one_color: bool = False) -> str:
    W, H = 64.0, 26.0
    doc = su.Doc(W, H)
    ink = Ink(base=WHITE if dark else INK_BLACK)
    base = ink.base
    if one_color:
        doc.color_map = {RED.lower(): base, PURPLE.lower(): base,
                         GREEN.lower(): base, TEAL.lower(): base}
        doc.gradient_mode, doc.gradient_colors = "flat", (base,)
    bar(doc, ink.red, 8, 6.5, 21, 6.5, 1.2)
    micro(doc, base, "SuperteamTR", x=8, y=14.6, size=4.6, tracking_em=0.24)
    micro(doc, base, "Solana Ecosystem \u00b7 Istanbul", x=8, y=20.6, size=3.0, tracking_em=0.22)
    su.place_logo(doc, logo("solanaLogo.svg"), x=56, y=7.5, width=26.0, align="end")
    return stamp(doc, "WHITE #FFFFFF | TR_RED #D6223B | Solana gradient printed as flat teal")


# --------------------------------------------------------------------------- #
#  CONCEPT 2 -- architectural blueprint / crypto network
# --------------------------------------------------------------------------- #


def build_concept2() -> str:
    W, H = 300.0, 380.0
    doc = su.Doc(W, H)
    B = INK_BLACK
    Rr = RED

    # sheet frame
    doc.path(su.frame_d(9, 9, W - 18, H - 18, 1.2), B)
    doc.path(su.frame_d(13.5, 13.5, W - 27, H - 27, 0.45), B)
    micro(doc, B, "SUPERTEAMTR // ARENA SECTION", x=16, y=24, size=4.2, tracking_em=0.30)
    micro(doc, B, "SHEET 02/03", x=W - 16, y=24, size=4.2, tracking_em=0.30, anchor="end")

    # ---- elevation of the arena: two arcade tiers + attic ---------------------
    y_ground = 250.0
    bar(doc, B, 22, y_ground, W - 22, y_ground, 1.0)          # ground line
    for x in range(30, 290, 18):                              # ground hatching
        bar(doc, B, x, y_ground, x + 7, y_ground + 7, 0.5)

    tiers = [dict(base=y_ground - 66, n=11, w=15.6, h=24.0, t=0.8),
             dict(base=y_ground - 22, n=13, w=13.6, h=20.0, t=0.75)]
    for ti, tier in enumerate(tiers):
        left = 26.0
        span = (W - 52.0) / tier["n"]
        for i in range(tier["n"]):
            ox = left + i * span + (span - tier["w"]) / 2.0
            pl = su.Place(ox, tier["base"], rot=0)
            doc.path(_apply(su._arch_local(tier["w"], tier["h"], tier["t"], 0.0), pl), B)
        bar(doc, B, 22, tier["base"], W - 22, tier["base"], 0.7)

    # attic + crown line
    bar(doc, B, 22, y_ground - 92, W - 22, y_ground - 92, 1.0)
    bar(doc, B, 30, y_ground - 104, W - 30, y_ground - 104, 0.7)
    for x in range(38, 268, 20):
        bar(doc, B, x, y_ground - 104, x, y_ground - 92, 0.45)
    for x in range(22, 279, 32):
        bar(doc, B, x, y_ground - 92, x, y_ground - 86, 0.45)

    # ---- dimension lines ------------------------------------------------------
    bar(doc, Rr, 22, y_ground - 118, W - 22, y_ground - 118, 0.45)
    for x, d in ((22, 1), (W - 22, -1)):
        bar(doc, Rr, x, y_ground - 118, x, y_ground - 125, 0.45)
        bar(doc, Rr, x, y_ground - 118, x, y_ground - 111, 0.45)
    micro(doc, Rr, "\u00d8 268 mm  /  11 BAYS x 2 TIERS", x=W / 2, y=y_ground - 122.5,
          size=4.0, tracking_em=0.24, anchor="middle")

    # centreline (dash-dot)
    for y in range(120, 262, 12):
        bar(doc, B, W / 2, y, W / 2, y + 7, 0.35)
    bar(doc, B, W / 2 - 6, 118, W / 2 + 6, 118, 0.35)

    # ---- network node graph (Solana-style cluster) ----------------------------
    nodes = [(233, 62), (263, 80), (238, 102), (270, 112), (249, 136),
             (216, 122), (205, 88), (44, 112), (68, 112), (56, 134), (84, 130)]
    links = [(0, 1), (0, 2), (1, 3), (2, 3), (2, 4), (3, 4), (2, 5), (5, 4),
             (0, 6), (6, 2), (7, 8), (8, 9), (7, 9), (9, 10), (10, 4), (10, 5)]
    for a, b in links:
        c = Rr if (a, b) in ((2, 3), (9, 10)) else B
        bar(doc, c, nodes[a][0], nodes[a][1], nodes[b][0], nodes[b][1], 0.5)
    for i, (x, y) in enumerate(nodes):
        c = Rr if i in (3, 10) else B
        dot(doc, c, x, y, 2.6)
        doc.path(su.ring_d(x, y, 5.6, 5.0), B)
    micro(doc, B, "NODE CLUSTER / VALIDATOR MESH", x=206, y=145, size=3.2, tracking_em=0.20)
    micro(doc, B, "LATENCY 400 MS / 2 TIERS", x=42, y=145, size=3.2, tracking_em=0.20)

    # ---- plan view (top) -----------------------------------------------------
    # small circular plan in the upper left of the sheet
    ccx, ccy, cR = 52.0, 56.0, 25.0
    doc.path(su.ring_d(ccx, ccy, cR, cR - 0.7), B)
    doc.path(su.ring_d(ccx, ccy, cR * 0.72, cR * 0.72 - 0.5), B)
    for i in range(24):
        a = i * 15.0
        p0 = su._polar(ccx, ccy, cR * 0.76, a)
        p1 = su._polar(ccx, ccy, cR * 0.95, a)
        bar(doc, B, p0[0], p0[1], p1[0], p1[1], 0.4)
    bar(doc, B, ccx - cR, ccy, ccx + cR, ccy, 0.4)
    bar(doc, B, ccx, ccy - cR, ccx, ccy + cR, 0.4)
    dot(doc, Rr, ccx, ccy, 2.0)
    micro(doc, B, "PLAN / ARENA", x=ccx, y=ccy + cR + 8, size=3.2, tracking_em=0.20, anchor="middle")

    # ---- brand block + title block -------------------------------------------
    su.place_logo(doc, logo("superteamtr-monogram.svg"), x=54.0, y=272.0,
                  width=50.0, align="center", recolor=B)
    micro(doc, B, "SuperteamTR", x=104.0, y=298.0, size=10.0, tracking_em=0.06,
          font="grotesk-700")
    bar(doc, B, 104.0, 302.0, 172.0, 302.0, 0.5)
    size = fit_size("display", "BUILD THE ARENA", 68.0, 0.10)
    text_path(doc, B, "BUILD THE ARENA", font="display", size=size, x=104.0, y=320.0,
              tracking=0.10 * size)
    su.place_logo(doc, logo("solanaLogo.svg"), x=104.0, y=326.0, width=56.0,
                  align="start", recolor=B)

    # title block (right)
    tb_x, tb_y, tb_w = 184.0, 272.0, 102.0
    doc.path(su.frame_d(tb_x, tb_y, tb_w, 62.0, 0.9), B)
    rows = [
        ("PROJECT", "SUPERTEAMTR T-SHIRT"),
        ("DRAWING", "ARENA ELEVATION / A-A"),
        ("SCALE", "1:10 / SHEET 02 OF 03"),
        ("ECOSYSTEM", "SOLANA / ISTANBUL, TR"),
        ("PRINT", "4 INK / 300 DPI MIN"),
    ]
    for i, (k, v) in enumerate(rows):
        y = tb_y + 10.0 + i * 10.4
        micro(doc, B, k, x=tb_x + 4.0, y=y, size=3.0, tracking_em=0.16)
        micro(doc, B, v, x=tb_x + tb_w - 4.0, y=y, size=3.0, tracking_em=0.16, anchor="end")
    bar(doc, B, 104.0, 340.0, 172.0, 340.0, 0.4)
    micro(doc, B, "CONNECT. CREATE. SHIP.", x=104.0, y=347.0, size=3.2, tracking_em=0.22)
    return stamp(doc, "one-colour on bone: BLUEPRINT_BLACK #0B0B10 + TR_RED #D6223B accent")


# --------------------------------------------------------------------------- #
#  CONCEPT 3 -- premium minimal seal
# --------------------------------------------------------------------------- #


def build_concept3(dark: bool = True) -> str:
    W = H = 300.0
    doc = su.Doc(W, H)
    ink = Ink(base=WHITE if dark else INK_BLACK)
    B = ink.base
    cx = cy = 138.0
    R = 104.0

    ring(doc, B, cx, cy, R, R - 1.3)
    ring(doc, B, cx, cy, R * 0.845, R * 0.845 - 1.0)
    for i in range(8):
        a = 22.5 + i * 45.0
        arch(doc, B, cx, cy, a, R * 0.90, R * 0.115, R * 0.10, R * 0.008)

    # circular micro type
    d = shaper("mono-500").circular_path(
        "SOLANA ECOSYSTEM", cx=cx, cy=cy, radius=R * 0.94, size=6.2,
        tracking=1.9, start_angle=0.0, direction=1)
    doc.path(d, B)
    d = shaper("mono-500").circular_path(
        "* BUILD TOGETHER *", cx=cx, cy=cy, radius=R * 0.94, size=6.2,
        tracking=1.9, start_angle=180.0, direction=-1, flip=True)
    doc.path(d, B)

    for s in (-1, 1):
        dot(doc, ink.red, cx + s * R * 0.94, cy, 2.6)

    # official SuperteamTR monogram + wordmark
    su.place_logo(doc, logo("superteamtr-monogram.svg"), x=cx, y=cy - 46.0, width=76.0,
                  align="center", recolor=B)
    micro(doc, B, "SuperteamTR", x=cx, y=cy + 52.0, size=17.0, tracking_em=0.14,
          font="grotesk-700", anchor="middle")
    su.place_logo(doc, logo("solanaLogo.svg"), x=cx, y=cy + 62.0, width=58.0, align="center")
    micro(doc, B, "ISTANBUL \u00b7 TR", x=cx, y=cy + 82.0, size=4.6, tracking_em=0.36,
          anchor="middle")
    return stamp(doc, "WHITE #FFFFFF | TR_RED #D6223B | Solana gradient #9945FF -> #14F195")


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #


FONT_FILES = ["Anton-Regular.ttf (Anton)", "SpaceGrotesk-VF.ttf (Space Grotesk)",
              "JetBrainsMono-VF.ttf (JetBrains Mono)"]


def stamp(doc: su.Doc, ink_note: str, fonts=None) -> su.Doc:
    doc.fonts = fonts or FONT_FILES
    doc.ink_note = ink_note
    return doc


def write_placements(svg_path: str, doc: su.Doc) -> None:
    import json
    if not doc.trace:
        return
    out = os.path.splitext(svg_path)[0] + ".placements.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({
            "_note": "Official brand assets embedded in this artwork file. The SVGs are "
                     "transformed rigidly (uniform scale + translate) and never redrawn.",
            "artwork": os.path.basename(svg_path),
            "print_size_mm": [doc.width, doc.height],
            "placements": doc.trace,
        }, fh, indent=2)
    print("   placements:", os.path.relpath(out, ROOT))


def write(path: str, doc) -> None:
    """Write the SVG plus a logo-placement provenance sidecar."""
    import json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = doc if isinstance(doc, str) else doc.svg()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote", os.path.relpath(path, ROOT))
    if not isinstance(doc, str) and doc.trace:
        sidecar = os.path.splitext(path)[0] + ".placements.json"
        with open(sidecar, "w", encoding="utf-8") as fh:
            json.dump({
                "_note": "Official brand assets embedded in this artwork file. The "
                         "supplied SVGs are transformed rigidly (uniform scale + "
                         "translation) and never redrawn, distorted or recoloured "
                         "(monochrome mode excepted, as an approved print fallback).",
                "artwork": os.path.basename(path),
                "print_size_mm": [doc.width, doc.height],
                "placements": doc.trace,
            }, fh, indent=2)
        print("   + placements sidecar")


def main() -> None:
    cdir = os.path.join(ROOT, "design", "concepts")
    fdir = os.path.join(ROOT, "design", "final")

    write(os.path.join(cdir, "concept-1-futuristic-arena.svg"), build_back_print(dark=True))
    write(os.path.join(cdir, "concept-2-blueprint-network.svg"), build_concept2())
    write(os.path.join(cdir, "concept-3-premium-minimal-seal.svg"), build_concept3(dark=True))

    write(os.path.join(fdir, "final-back-print-on-dark.svg"), build_back_print(dark=True))
    write(os.path.join(fdir, "final-back-print-on-light.svg"), build_back_print(dark=False))
    write(os.path.join(fdir, "final-front-chest-on-dark.svg"), build_front_chest(dark=True))
    write(os.path.join(fdir, "final-front-chest-on-light.svg"), build_front_chest(dark=False))
    write(os.path.join(fdir, "final-neck-label-on-dark.svg"), build_neck_label(dark=True))
    write(os.path.join(fdir, "final-sleeve-mark-on-dark.svg"), build_sleeve_mark(dark=True))

    # ---- production variants ------------------------------------------------- #
    pdir = os.path.join(ROOT, "production", "svg")
    meta = [
        ("final-back-print_on-dark_PRINTBUILD.svg",
         build_back_print(dark=True, gradient="print")),
        ("final-back-print_on-light_PRINTBUILD.svg",
         build_back_print(dark=False, gradient="print")),
        ("final-back-print_on-dark_1COLOR.svg",
         build_back_print(dark=True, one_color=True)),
        ("final-back-print_on-light_1COLOR.svg",
         build_back_print(dark=False, one_color=True)),
        ("final-back-print_on-dark_2COLOR.svg",
         build_back_print(dark=True, two_color=True)),
        ("final-back-print_on-light_2COLOR.svg",
         build_back_print(dark=False, two_color=True)),
        ("final-front-chest_on-dark_PRINTBUILD.svg",
         build_front_chest(dark=True, gradient="print")),
        ("final-front-chest_on-light_PRINTBUILD.svg",
         build_front_chest(dark=False, gradient="print")),
        ("final-front-chest_on-dark_1COLOR.svg",
         build_front_chest(dark=True, one_color=True)),
        ("final-front-chest_on-light_1COLOR.svg",
         build_front_chest(dark=False, one_color=True)),
        ("final-neck-label_on-dark_1COLOR.svg", build_neck_label(dark=True, one_color=True)),
        ("final-neck-label_on-light_1COLOR.svg", build_neck_label(dark=False, one_color=True)),
        ("final-sleeve-mark_on-dark_1COLOR.svg", build_sleeve_mark(dark=True, one_color=True)),
        ("final-sleeve-mark_on-light_1COLOR.svg", build_sleeve_mark(dark=False, one_color=True)),
    ]
    for name, content in meta:
        write(os.path.join(pdir, name), content)


if __name__ == "__main__":
    main()
