"""
build_mockups.py -- professional apparel mockups for the SuperteamTR T-shirt.

Garments are drawn procedurally (flat-shaded with fabric grain, collar rib, sleeve
and hem seams, soft folds) and the artwork is composited with an alpha mask so the
mockup never hides or re-draws the actual artwork: what you see is the real
production file at the real print scale.

Outputs (mockups/):
  mockup-front-view.png            dark garment, front chest print
  mockup-back-view.png             dark garment, full back print
  mockup-flatlay-back.png          light garment, flat lay, back print
  mockup-detail-closeup.png        print-quality close-up (1:1 print detail)
  mockup-dark-garment.png          dark garment back (print-scale reference)
  mockup-light-garment.png         light garment back (alt colourway)
  artwork-only-neutral.png         artwork only, neutral background
  mockup-print-placement.png       technical placement diagram (front + back)

Run:  python3 tools/build_mockups.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cairosvg                                     # noqa: E402
import numpy as np                                  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter       # noqa: E402

from lib.inks import INK                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mockups")

# ---- garment spec (adult unisex size L, drawn flat) ------------------------ #
TEE_W_MM = 520.0        # chest width (L)
TEE_H_MM = 720.0        # body length
PRINT_BACK_MM = (320.0, 400.0)
PRINT_FRONT_MM = (90.0, 104.0)
BACK_TOP_MM = 95.0      # neck-to-print distance for the back print
FRONT_TOP_MM = 95.0     # shoulder seam -> front chest print
FRONT_LEFT_MM = 95.0    # print offset from garment centre (wearer's right chest)


def p(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# --------------------------------------------------------------------------- #
#  procedural garment
# --------------------------------------------------------------------------- #
#
#  All garment geometry is authored in millimetres (adult unisex size L,
#  flat-laid) and converted to pixels with one scale factor, so the print can
#  be composited at its true physical size.


def _bez(p0, p1, p2, n=48):
    return [
        ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
         (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
        for t in np.linspace(0, 1, n)
    ]


# mm landmarks: x = 0 is the garment centre, y = 0 is the shoulder line
TEE_MM = dict(
    shoulder_x=250.0, shoulder_y=4.0,
    neck_x=92.0, neck_y=26.0, neck_c=30.0, neck_c_front=78.0,
    sleeve_top=(-292.0, 60.0), sleeve_cuff=(-296.0, 262.0), cuff_in=(-226.0, 272.0),
    armpit=(-255.0, 205.0),
    hem_x=258.0, hem_y=700.0, hem_c=720.0,
    body_check=216.0,
)

CANVAS_MM = (700.0, 800.0)       # mockup canvas incl. margin
SHOULDER_Y_MM = 40.0             # shoulder line inside the canvas
CENTRE_X_MM = 350.0


def mm2px(x_mm: float, y_mm: float, scale: float) -> tuple[float, float]:
    return (CENTRE_X_MM + x_mm) * scale, (SHOULDER_Y_MM + y_mm) * scale


def tee_outline(scale: float, view: str = "back"):
    """Closed garment outline.

    The left half is drawn with smooth curves from the centre-front/top point down
    to the centre of the hem; the right half is that same path mirrored, so the
    silhouette is perfectly symmetrical and never self-intersects.
    """
    L = TEE_MM
    P = lambda x, y: mm2px(x, y, scale)  # noqa: E731
    neck_drop = L["neck_c"] if view == "back" else L["neck_c_front"]

    half: list[tuple[float, float]] = []
    half += _bez(P(0.0, neck_drop), P(-58.0, neck_drop), P(-L["neck_x"], L["neck_y"]))
    half += _bez(P(-L["neck_x"], L["neck_y"]), P(-176.0, 5.0), P(-L["shoulder_x"], L["shoulder_y"]))
    half += _bez(P(-L["shoulder_x"], L["shoulder_y"]), P(-300.0, 118.0), P(*L["sleeve_cuff"]))
    half += _bez(P(*L["sleeve_cuff"]), P(-274.0, 276.0), P(*L["cuff_in"]))
    half += _bez(P(*L["cuff_in"]), P(-214.0, 248.0), P(*L["armpit"]))
    half += _bez(P(*L["armpit"]), P(-263.0, 430.0), P(-L["hem_x"], L["hem_y"]))
    half += _bez(P(-L["hem_x"], L["hem_y"]), P(-118.0, L["hem_c"]), P(0.0, L["hem_c"]), 60)

    mirror_x = 2.0 * CENTRE_X_MM * scale
    right = [(-x + mirror_x, y) for x, y in (half + [P(0.0, neck_drop)])]
    outline = half + list(reversed(right))
    # drop the duplicated centre points at the hem and the neck
    return outline


def render_tee(colour: str, scale: float = 2.7, view: str = "back"):
    """Return (garment RGBA image, alpha mask). scale = px per mm."""
    W = int(CANVAS_MM[0] * scale)
    H = int(CANVAS_MM[1] * scale)
    base = hex_rgb(colour)
    pts = tee_outline(scale, view)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))

    # base shading: light from the upper left, soft side falloff
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W, yy / H
    shade = 0.88 + 0.20 * (1.0 - v) ** 1.2
    shade *= 1.0 - 0.26 * np.clip(np.abs(u - 0.5) * 2.15 - 0.62, 0, 1) ** 1.5
    shade += 0.05 * np.exp(-(((u - 0.40) ** 2) / 0.02 + ((v - 0.26) ** 2) / 0.05))
    arr = np.zeros((H, W, 4), dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = np.clip(base[i] * shade, 0, 255)
    arr[:, :, 3] = np.asarray(mask, dtype=np.float32)

    # fabric grain (knit weave feel)
    rng = np.random.default_rng(11)
    grain = rng.normal(0, 3.4, (H, W)).astype(np.float32)
    grain = np.asarray(Image.fromarray(((grain + 8) * 6).clip(0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(0.5)), dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = np.clip(arr[:, :, i] + (grain - 48) * 0.30, 0, 255)

    garment = Image.fromarray(arr.round().astype(np.uint8), "RGBA")

    # soft folds
    folds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(folds)
    for (a, b, bow, wfac) in ((0.24, 0.31, 0.05, 0.9), (0.69, 0.76, -0.05, 0.9),
                              (0.445, 0.53, 0.03, 0.7), (0.31, 0.38, -0.02, 0.6)):
        pts_f = _bez((W * a, H * 0.46), (W * ((a + b) / 2 + bow), H * 0.68),
                     (W * b, H * 0.945), 40)
        fd.line(pts_f, fill=(0, 0, 0, 20), width=int(W * 0.013 * wfac), joint="curve")
    folds = folds.filter(ImageFilter.GaussianBlur(W * 0.010))
    garment = Image.alpha_composite(garment, Image.composite(folds, Image.new("RGBA", (W, H)), mask))

    # stitching and rib detail: drawn on an overlay, clipped to the silhouette,
    # then composited -- so nothing can ever appear outside the garment
    detail = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(detail, "RGBA")
    dark = (max(base[0] - 30, 0), max(base[1] - 30, 0), max(base[2] - 30, 0), 150)
    stitch = (min(base[0] + 26, 255), min(base[1] + 26, 255), min(base[2] + 26, 255), 95)
    rib_col = (min(base[0] + 14, 255), min(base[1] + 14, 255), min(base[2] + 14, 255), 165)
    lw = max(2, int(scale * 2.0))

    # neck rib band (a ribbed collar ring)
    neck_drop = TEE_MM["neck_c"] if view == "back" else TEE_MM["neck_c_front"]
    outer = [mm2px(0.0, neck_drop - 12.0, scale)] + _bez(
        mm2px(0.0, neck_drop - 12.0, scale), mm2px(-58.0, neck_drop - 12.0, scale),
        mm2px(-TEE_MM["neck_x"] - 4.0, TEE_MM["neck_y"] - 5.0, scale))
    inner = list(reversed([mm2px(0.0, neck_drop, scale)] + _bez(
        mm2px(0.0, neck_drop, scale), mm2px(-58.0, neck_drop, scale),
        mm2px(-TEE_MM["neck_x"], TEE_MM["neck_y"], scale))))
    mirror_x = 2.0 * CENTRE_X_MM * scale
    for side in (1, -1):
        poly = outer + inner
        if side < 0:
            poly = [(-x + mirror_x, y) for x, y in poly]
        d.polygon(poly, fill=rib_col)
    # seam line where the rib meets the body
    for side in (1, -1):
        seam_curve = [mm2px(0.0, neck_drop + 12.0, scale)] + _bez(
            mm2px(0.0, neck_drop + 12.0, scale), mm2px(-58.0, neck_drop + 12.0, scale),
            mm2px(-TEE_MM["neck_x"] + 5.0, TEE_MM["neck_y"] + 7.0, scale), 30)
        if side < 0:
            seam_curve = [(-x + mirror_x, y) for x, y in seam_curve]
        d.line(seam_curve, fill=dark, width=max(1, lw - 1), joint="curve")

    sx = lambda x: mm2px(x, 0.0, scale)[0]      # noqa: E731
    sy = lambda y: mm2px(0.0, y, scale)[1]      # noqa: E731
    for side in (1, -1):
        seam = _bez((sx(side * 248.0), sy(7.0)), (sx(side * 238.0), sy(120.0)),
                    (sx(side * 216.0), sy(203.0)), 30)
        d.line(seam, fill=dark, width=max(1, lw - 1), joint="curve")
        d.line([(sx(side * 296.0), sy(261.0)), (sx(side * 226.0), sy(271.0))],
               fill=stitch, width=max(1, lw - 1))
    d.line(_bez(mm2px(-TEE_MM["hem_x"], TEE_MM["hem_y"] - 12.0, scale),
                mm2px(0.0, TEE_MM["hem_c"] - 12.0, scale),
                mm2px(TEE_MM["hem_x"], TEE_MM["hem_y"] - 12.0, scale), 60),
           fill=stitch, width=max(1, lw - 1), joint="curve")

    # clip all detail to the garment silhouette
    det = np.asarray(detail).astype(np.float32)
    det[:, :, 3] *= np.asarray(mask, dtype=np.float32) / 255.0
    detail = Image.fromarray(det.round().astype(np.uint8), "RGBA")
    garment = Image.alpha_composite(garment, detail)

    return garment, mask


# --------------------------------------------------------------------------- #
#  compositing
# --------------------------------------------------------------------------- #


def artwork_layer(svg_path: str, print_mm: tuple[float, float], px_per_mm: float) -> Image.Image:
    """Rasterise the master SVG at exactly the print scale (px_per_mm)."""
    w_px = int(round(print_mm[0] * px_per_mm))
    tmp = "/tmp/_mock_art.png"
    cairosvg.svg2png(url=svg_path, write_to=tmp, output_width=w_px, background_color=None)
    return Image.open(tmp).convert("RGBA")


def place_print(garment: Image.Image, art: Image.Image, *, px_per_mm: float,
                top_mm: float, left_mm: float = 0.0) -> Image.Image:
    """Composite artwork on the garment: physical offsets from the shoulder line
    and the garment centre line, at the true print scale."""
    w, h = garment.size
    top_px = int(round((SHOULDER_Y_MM + top_mm) * px_per_mm))
    left_px = int(round((CENTRE_X_MM + left_mm) * px_per_mm - art.width / 2))
    layer = Image.new("RGBA", garment.size, (0, 0, 0, 0))
    layer.alpha_composite(art, (left_px, top_px))
    # fabric texture over the ink so the print sits "in" the cloth
    arr = np.asarray(layer).astype(np.float32)
    keep = arr[:, :, 3] > 0
    if keep.any():
        noise = np.random.default_rng(3).normal(0, 5.0, arr.shape[:2]).astype(np.float32)
        for i in range(3):
            arr[:, :, i] = np.where(keep, np.clip(arr[:, :, i] + noise * 0.35, 0, 255), arr[:, :, i])
    layer = Image.fromarray(arr.round().astype(np.uint8), "RGBA")
    return Image.alpha_composite(garment, layer)


def make_background(size, colour=(238, 238, 236)):
    w, h = size
    top = np.array(colour, dtype=np.float32)
    bottom = np.clip(top * 0.86, 0, 255)
    grad = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    arr = (top[None, None, :] * (1 - grad) + bottom[None, None, :] * grad)
    arr = np.repeat(arr, w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def compose(garment: Image.Image, bg_colour=(238, 238, 236), pad_frac=0.06,
            drop_shadow=True) -> Image.Image:
    w, h = garment.size
    pad = int(w * pad_frac)
    canvas = make_background((w + 2 * pad, h + 2 * pad), bg_colour)
    if drop_shadow:
        alpha = garment.split()[3].filter(ImageFilter.GaussianBlur(w * 0.020))
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        solid = Image.new("RGBA", garment.size, (0, 0, 0, 46))
        sh.paste(solid, (pad + int(w * 0.004), pad + int(h * 0.008)), alpha)
        # keep the shadow below the shoulder line so nothing appears above the collar
        cutoff = pad + int(h * 0.075)
        sh_np = np.asarray(sh).astype(np.float32)
        sh_np[:cutoff, :, 3] = 0
        sh = Image.fromarray(sh_np.round().astype(np.uint8), "RGBA")
        canvas = Image.alpha_composite(canvas.convert("RGBA"), sh).convert("RGB")
    canvas.paste(garment, (pad, pad), garment)
    return canvas


# --------------------------------------------------------------------------- #
#  individual mockups
# --------------------------------------------------------------------------- #


def _garment(scale: float, colour: str, view: str) -> Image.Image:
    garment, _ = render_tee(colour, scale, view)
    return garment


def mock_back_view(colour: str, out: str, bg=(236, 236, 234), art_svg=None,
                   scale: float = 2.7) -> None:
    garment = _garment(scale, colour, "back")
    art = artwork_layer(art_svg or p("design", "final", "final-back-print-on-dark.svg"),
                        PRINT_BACK_MM, scale)
    garment = place_print(garment, art, px_per_mm=scale, top_mm=BACK_TOP_MM)
    compose(garment, bg).save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def mock_front_view(colour: str, out: str, bg=(236, 236, 234), art_svg=None,
                    scale: float = 2.7) -> None:
    garment = _garment(scale, colour, "front")
    art = artwork_layer(art_svg or p("design", "final", "final-front-chest-on-dark.svg"),
                        PRINT_FRONT_MM, scale)
    # wearer's right chest = viewer's left on a front view
    garment = place_print(garment, art, px_per_mm=scale, top_mm=FRONT_TOP_MM,
                          left_mm=-(FRONT_LEFT_MM + PRINT_FRONT_MM[0] / 2))
    compose(garment, bg).save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def mock_flatlay(colour: str, out: str, bg=(243, 240, 233), scale: float = 2.6) -> None:
    garment = _garment(scale, colour, "back")
    light = colour.lower() == INK["GARMENT_OFF_WHITE"]["hex"].lower()
    art = artwork_layer(p("design", "final",
                          "final-back-print-on-light.svg" if light
                          else "final-back-print-on-dark.svg"), PRINT_BACK_MM, scale)
    garment = place_print(garment, art, px_per_mm=scale, top_mm=BACK_TOP_MM)
    composed = compose(garment, bg, pad_frac=0.05, drop_shadow=True)
    composed = composed.rotate(-1.2, resample=Image.BICUBIC, expand=False, fillcolor=tuple(bg))
    composed.save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def mock_detail(out: str, cloth: str | None = None) -> None:
    """1:1 print detail: 110 x 62 mm of the back print, magnified 2x."""
    px_per_mm = 12.0
    svg = p("design", "final", "final-back-print-on-dark.svg")
    tmp = "/tmp/_detail_full.png"
    cairosvg.svg2png(url=svg, write_to=tmp, output_width=int(PRINT_BACK_MM[0] * px_per_mm),
                     background_color=cloth or INK["GARMENT_WASHED_BLACK"]["hex"])
    full = Image.open(tmp).convert("RGB")
    cx = full.width // 2
    top = int(full.height * 0.28)
    crop = full.crop((cx - int(55 * px_per_mm), top, cx + int(55 * px_per_mm),
                      top + int(62 * px_per_mm)))
    # fabric grain over the crop so print and cloth feel like one surface
    arr = np.asarray(crop).astype(np.float32)
    rng = np.random.default_rng(5)
    arr = np.clip(arr + rng.normal(0, 3.0, arr.shape).astype(np.float32), 0, 255)
    crop = Image.fromarray(arr.round().astype(np.uint8), "RGB")
    crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
    crop.save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def artwork_only(out: str) -> None:
    svg = p("design", "final", "final-back-print-on-dark.svg")
    tmp = "/tmp/_art_only.png"
    cairosvg.svg2png(url=svg, write_to=tmp, output_width=2400, background_color=None)
    art = Image.open(tmp).convert("RGBA")
    pad = 140
    canvas = Image.new("RGB", (art.width + 2 * pad, art.height + 2 * pad), (126, 126, 128))
    canvas.paste(art, (pad, pad), art)
    canvas.save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def artwork_only_light(out: str) -> None:
    svg = p("design", "final", "final-back-print-on-light.svg")
    tmp = "/tmp/_art_only_light.png"
    cairosvg.svg2png(url=svg, write_to=tmp, output_width=2400, background_color=None)
    art = Image.open(tmp).convert("RGBA")
    pad = 140
    canvas = Image.new("RGB", (art.width + 2 * pad, art.height + 2 * pad), (206, 203, 196))
    canvas.paste(art, (pad, pad), art)
    canvas.save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def placement_diagram(out: str) -> None:
    """Technical front/back placement sheet with all measurements."""
    W, H = 2200, 1500
    img = make_background((W, H), (245, 245, 243)).convert("RGBA")
    d = ImageDraw.Draw(img)
    try:
        from PIL import ImageFont
        font = ImageFont.load_default(size=22)
        font_small = ImageFont.load_default(size=19)
        font_head = ImageFont.load_default(size=30)
    except Exception:  # pragma: no cover
        font = font_small = font_head = None

    scale = 1.55

    def stamp(view, cx_px):
        g, _ = render_tee(INK["GARMENT_WASHED_BLACK"]["hex"], scale, view)
        img.alpha_composite(g, (int(cx_px - CENTRE_X_MM * scale), 120))
        return g

    d.text((60, 40), "SuperteamTR T-Shirt — print placement (adult unisex size L)",
           fill=(20, 20, 20), font=font_head)

    specs = [
        ("BACK", 620, [("back", 320, 400, 95.0, 0.0)], (214, 34, 59)),
        ("FRONT", 1600, [("front", 90, 104, 95.0, -95.0)], (214, 34, 59)),
    ]
    for label, cx_px, prints, col in specs:
        stamp("back" if label == "BACK" else "front", cx_px)
        for _kind, pw, ph, top_mm, left_mm in prints:
            x0 = cx_px + (left_mm - pw / 2) * scale
            y0 = 120 + (SHOULDER_Y_MM + top_mm) * scale
            box = [x0, y0, x0 + pw * scale, y0 + ph * scale]
            d.rectangle(box, outline=col, width=4)
            d.line([(cx_px, box[1]), (cx_px, box[3])], fill=col, width=2)
            d.text((box[0], box[1] - 32), f"{pw:.0f} × {ph:.0f} mm  PRINT", fill=col, font=font)
            arrow_x = box[0] - 70
            d.line([(arrow_x, 120 + SHOULDER_Y_MM * scale), (arrow_x, box[1])], fill=(30, 30, 30), width=3)
            d.line([(arrow_x - 10, box[1]), (arrow_x + 10, box[1])], fill=(30, 30, 30), width=3)
            d.text((arrow_x - 66, (120 + SHOULDER_Y_MM * scale + box[1]) / 2), f"{top_mm:.0f} mm",
                   fill=(30, 30, 30), font=font_small)
        if label == "FRONT":
            d.line([(cx_px, 120 + SHOULDER_Y_MM * scale), (cx_px, 120 + 720 * scale)],
                   fill=(120, 120, 120), width=2)
            d.text((cx_px + 8, 120 + 400 * scale), "centre line", fill=(110, 110, 110), font=font_small)
        d.text((cx_px - 60, 120 + 790 * scale), label, fill=(20, 20, 20), font=font_head)

    notes = [
        "Back print: 320 × 400 mm, centred on the body, 95 mm below the neck rib (2 cm below the yoke seam).",
        "Front left-chest mark: 90 × 104 mm, 95 mm below the shoulder seam, 95 mm offset from centre (wearer's right).",
        "Neck label: 64 × 26 mm printed inside the back neck. Optional sleeve mark: 40 mm circle.",
        "Garment: washed black 220–260 gsm combed cotton (alternative: bone / natural).",
        "Every element keeps a 25 mm margin from the nearest seam so the print never breaks over an edge.",
    ]
    for i, note in enumerate(notes):
        d.text((60, H - 190 + i * 32), note, fill=(40, 40, 40), font=font_small)
    img.convert("RGB").save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def mock_concept(art_rel: str, out: str, *, colour: str, view: str = "back",
                 print_mm=(300.0, 380.0), top_mm: float = 95.0, bg=(238, 236, 232),
                 scale: float = 2.5) -> None:
    """Generic garment preview for a concept artwork file."""
    garment = _garment(scale, colour, view)
    art = artwork_layer(p(*art_rel.split("/")), print_mm, scale)
    garment = place_print(garment, art, px_per_mm=scale, top_mm=top_mm)
    composed = compose(garment, bg, pad_frac=0.055, drop_shadow=True)
    composed = composed.rotate(-0.8, resample=Image.BICUBIC, expand=False, fillcolor=tuple(bg))
    composed.save(out)
    print("  ✓", os.path.relpath(out, ROOT))


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    dark = INK["GARMENT_WASHED_BLACK"]["hex"]
    light = INK["GARMENT_OFF_WHITE"]["hex"]

    mock_back_view(dark, p("mockups", "mockup-back-view.png"))
    mock_front_view(dark, p("mockups", "mockup-front-view.png"))
    mock_back_view(dark, p("mockups", "mockup-dark-garment.png"), bg=(232, 232, 230))
    mock_back_view(light, p("mockups", "mockup-light-garment.png"), bg=(236, 234, 228),
                   art_svg=p("design", "final", "final-back-print-on-light.svg"))
    mock_flatlay(light, p("mockups", "mockup-flatlay-back.png"))
    mock_flatlay(dark, p("mockups", "mockup-flatlay-dark.png"), bg=(228, 228, 226))
    mock_detail(p("mockups", "mockup-detail-closeup.png"))
    artwork_only(p("mockups", "artwork-only-neutral.png"))
    artwork_only_light(p("mockups", "artwork-only-light.png"))
    placement_diagram(p("mockups", "mockup-print-placement.png"))

    # ---- concept directions (deliverable A needs a mockup preview each) ------ #
    mock_concept("design/concepts/concept-1-futuristic-arena.svg",
                 p("mockups", "concept-1-mockup-back.png"), colour=dark,
                 print_mm=(320.0, 400.0))
    mock_concept("design/concepts/concept-2-blueprint-network.svg",
                 p("mockups", "concept-2-mockup-back.png"), colour=light,
                 print_mm=(280.0, 355.0), top_mm=110.0, bg=(240, 236, 226))
    mock_concept("design/concepts/concept-3-premium-minimal-seal.svg",
                 p("mockups", "concept-3-mockup-front.png"), colour=dark, view="front",
                 print_mm=(210.0, 210.0), top_mm=140.0)


if __name__ == "__main__":
    main()
