"""
build_production.py -- turns the master SVGs into the production file package.

Outputs (all regenerated from design/ + production/svg masters):
  production/pdf-cmyk/          vector CMYK PDFs (full colour / print build / 2-ink / 1-ink)
  production/eps-cmyk/          the same as editable EPS (CMYK, Illustrator/InDesign ready)
  production/separations/       one vector film per screen-print ink (+ underbase/union plate)
  production/png-300dpi/        transparent PNGs, >=300 dpi, exact print size
  production/tiff-300dpi/       CMYK soft-proof TIFFs (naive sRGB->CMYK build, documented)
  production/psd/               layered PSD (ink separations + master + garments + guides)
  production/colour-palette.json

Run:  python3 tools/build_production.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cairosvg                      # noqa: E402
import numpy as np                   # noqa: E402
from PIL import Image, ImageDraw     # noqa: E402

from lib.inks import (GRADIENT_PRINT_MAP, HERO_SEPARATIONS, INK,   # noqa: E402
                      hex_to_rgb, rgb_to_cmyk)
from lib.pathparse import subpaths_to_d                          # noqa: E402
from lib.vector_export import svg_to_eps, svg_to_pdf              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WHITE = INK["WHITE"]["hex"]
RED = INK["TR_RED"]["hex"]
PURPLE = INK["SOLANA_PURPLE"]["hex"]
GREEN = INK["SOLANA_GREEN"]["hex"]
TEAL = INK["SOLANA_TEAL"]["hex"]
BLACK_INK = INK["BLUEPRINT_BLACK"]["hex"]

PNG_DPI = 300


def p(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def mm_to_px(mm: float, dpi: int = PNG_DPI) -> int:
    return int(round(mm / 25.4 * dpi))


# --------------------------------------------------------------------------- #
#  raster helpers
# --------------------------------------------------------------------------- #


def rasterize(svg_text: str, out_png: str, width_mm: float, height_mm: float,
              dpi: int = PNG_DPI, background: str | None = None) -> str:
    w = mm_to_px(width_mm, dpi)
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=out_png,
                     output_width=w, background_color=background)
    return out_png


def to_cmyk_tiff(src_png: str, out_tiff: str, dpi: int = PNG_DPI) -> None:
    """Naive sRGB -> CMYK build (documented as a soft proof).

    Photoshop/Illustrator should re-separate with the printer's ICC profile
    (e.g. Coated FOGRA39); every ink's target build is listed in
    production/colour-palette.json.
    """
    im = Image.open(src_png).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im).convert("RGB")
    arr = np.asarray(im).astype(np.float32) / 255.0
    k = 1.0 - arr.max(axis=2)
    denom = np.where(k >= 0.999, 1.0, 1.0 - k)
    c = (1.0 - arr[:, :, 0] - k) / denom
    m = (1.0 - arr[:, :, 1] - k) / denom
    y = (1.0 - arr[:, :, 2] - k) / denom
    out = np.dstack([np.clip(c, 0, 1), np.clip(m, 0, 1), np.clip(y, 0, 1), np.clip(k, 0, 1)])
    cmyk = Image.fromarray((out * 255).round().astype(np.uint8), mode="CMYK")
    cmyk.save(out_tiff, compression="tiff_lzw", dpi=(dpi, dpi),
              description="CMYK soft proof - naive sRGB build, re-separate with printer ICC")


def ink_mask(svg_text: str, colour: str, width_mm: float, height_mm: float,
             dpi: int = 150) -> Image.Image:
    """1-bit-ish coverage mask (L mode, 255 = ink) for one flat ink colour."""
    from lib.vector_export import read_svg
    doc = read_svg(svg_text)
    w, h = mm_to_px(width_mm, dpi), mm_to_px(height_mm, dpi)
    canvas = np.zeros((h, w), dtype=np.uint8)
    import cairosvg
    from xml.sax.saxutils import escape
    keep = []
    for it in doc.items:
        cols = [it.fill]
        if it.gradient:
            cols += [c for _o, c in it.gradient["stops"]]
        if colour.lower() in [c.lower() for c in cols]:
            keep.append(f'<path d="{subpaths_to_d(it.subpaths)}" fill="#000000" '
                        f'fill-rule="evenodd"/>')
    if not keep:
        return Image.fromarray(canvas, mode="L")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" '
           f'height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">'
           + "".join(keep) + "</svg>")
    tmp = "/tmp/_mask.png"
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=tmp, output_width=w,
                     background_color="#FFFFFF")
    a = np.asarray(Image.open(tmp).convert("L"))
    canvas = 255 - a            # ink = white in the mask
    return Image.fromarray(canvas, mode="L")


# --------------------------------------------------------------------------- #
#  PSD (layered)
# --------------------------------------------------------------------------- #


def build_psd(svg_rel: str, out_path: str, width_mm: float, height_mm: float,
              garment: str, *, label: str = "", dpi: int = 100) -> bool:
    """Layered PSD: garment guide, one spot layer per ink, print guide, hidden master.

    Layers are named after the Pantone spot inks so the file maps 1:1 onto the
    spot-colour PDF/EPS set.
    """
    try:
        from psd_tools import PSDImage
    except Exception as exc:  # pragma: no cover
        print("  ! psd-tools unavailable:", exc)
        return False

    svg_text = read(svg_rel)
    w, h = mm_to_px(width_mm, dpi), mm_to_px(height_mm, dpi)
    try:
        psd = PSDImage.new(mode="RGB", size=(w, h))
    except Exception as exc:  # pragma: no cover
        print("  ! PSDImage.new unsupported:", exc)
        return False

    def add(name: str, arr: np.ndarray, visible=True):
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[:, :, :3] = arr[:, :, :3]
        rgba[:, :, 3] = arr[:, :, 3]
        layer = psd.create_pixel_layer(Image.fromarray(rgba, "RGBA"), name=name,
                                       top=0, left=0, opacity=255)
        layer.visible = visible
        psd.append(layer)

    # garment guide (bottom layer)
    g = np.zeros((h, w, 4), dtype=np.uint8)
    gr, gg, gb = hex_to_rgb(garment)
    g[:, :, 0], g[:, :, 1], g[:, :, 2], g[:, :, 3] = gr, gg, gb, 255
    add("00_GARMENT_GUIDE (" + garment + ")", g)

    # one layer per spot ink, in print order
    order = [("WHITE", "WHITE_underbase"), ("BLUEPRINT_BLACK", "BLUEPRINT_BLACK"),
             ("TR_RED", "TR_RED"), ("SOLANA_PURPLE", "SOLANA_PURPLE"),
             ("SOLANA_TEAL", "SOLANA_TEAL"), ("SOLANA_GREEN", "SOLANA_GREEN")]
    idx = 0
    for key, layer_tag in order:
        colour = INK[key]["hex"]
        m = np.asarray(ink_mask(svg_text, colour, width_mm, height_mm, dpi), dtype=np.uint8)
        if m.max() == 0:
            continue
        idx += 1
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        r, gch, b = hex_to_rgb(colour)
        rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2] = r, gch, b
        rgba[:, :, 3] = m
        name = f"{idx:02d}_SPOT_{INK[key]['spot'].replace(' ', '_')}"
        add(name, rgba)

    # print guide: bleed box, trim box, registration crosses (never printed)
    guide = np.zeros((h, w, 4), dtype=np.uint8)
    gi = Image.fromarray(guide, "RGBA")
    gd = ImageDraw.Draw(gi)
    pad_x, pad_y = int(w * 0.06), int(h * 0.05)
    gd.rectangle([pad_x, pad_y, w - pad_x, h - pad_y], outline=(255, 0, 255, 190),
                 width=max(2, int(dpi * 0.12)))
    arm = int(min(w, h) * 0.03)
    w2 = max(1, int(dpi * 0.10))
    for cx_, cy_ in ((pad_x, pad_y), (w - pad_x, pad_y), (pad_x, h - pad_y), (w - pad_x, h - pad_y)):
        gd.line([(cx_ - arm, cy_), (cx_ + arm, cy_)], fill=(0, 200, 255, 200), width=w2)
        gd.line([(cx_, cy_ - arm), (cx_, cy_ + arm)], fill=(0, 200, 255, 200), width=w2)
    add(f"{idx + 1:02d}_PRINT_GUIDE_{width_mm:.0f}x{height_mm:.0f}mm_at_{dpi}dpi_do-not-print",
        np.asarray(gi))

    # flattened master reference (hidden)
    tmp = "/tmp/_master.png"
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=tmp,
                     output_width=w, background_color=None)
    master = np.asarray(Image.open(tmp).convert("RGBA"), dtype=np.uint8)
    add(f"{idx + 2:02d}_MASTER_REFERENCE_do-not-print", master, visible=False)

    try:
        psd.save(out_path, compress=True)
    except TypeError:
        psd.save(out_path)
    return True


def build_panels_psd(out_path: str, dpi: int = 70) -> bool:
    """One 1:1 layout sheet holding every printed panel as its own layer."""
    try:
        from psd_tools import PSDImage
    except Exception as exc:  # pragma: no cover
        print("  ! psd-tools unavailable:", exc)
        return False

    panels = [
        ("BACK_PRINT_320x400", "production/svg/final-back-print_on-dark_PRINTBUILD.svg", 320.0, 400.0, 20.0, 30.0),
        ("FRONT_CHEST_90x104", "production/svg/final-front-chest_on-dark_PRINTBUILD.svg", 90.0, 104.0, 360.0, 30.0),
        ("NECK_LABEL_64x26", "production/svg/final-neck-label_on-dark_1COLOR.svg", 64.0, 26.0, 360.0, 160.0),
        ("SLEEVE_MARK_44x44", "production/svg/final-sleeve-mark_on-dark_1COLOR.svg", 44.0, 44.0, 360.0, 210.0),
    ]
    canvas_mm = (520.0, 460.0)
    W = mm_to_px(canvas_mm[0], dpi)
    H = mm_to_px(canvas_mm[1], dpi)
    try:
        psd = PSDImage.new(mode="RGB", size=(W, H))
    except Exception as exc:  # pragma: no cover
        print("  ! PSDImage.new unsupported:", exc)
        return False

    def add(name, arr, visible=True):
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[:, :, :3] = arr[:, :, :3]
        rgba[:, :, 3] = arr[:, :, 3]        # keep true alpha: guides stay transparent
        layer = psd.create_pixel_layer(Image.fromarray(rgba, "RGBA"), name=name,
                                       top=0, left=0, opacity=255)
        layer.visible = visible
        psd.append(layer)

    # paper background (this one is intentionally opaque)
    bg = np.zeros((H, W, 4), dtype=np.uint8)
    bg[:, :, :3] = 247
    bg[:, :, 3] = 255
    sheet = psd.create_pixel_layer(Image.fromarray(bg, "RGBA"), name="00_SHEET_520x460mm",
                                   top=0, left=0, opacity=255)
    sheet.visible = True
    psd.append(sheet)

    guide = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(guide)
    for name, src, pw, ph, x, y in panels:
        px = int(x * dpi / 25.4)
        py = int(y * dpi / 25.4)
        ww, hh = int(pw * dpi / 25.4), int(ph * dpi / 25.4)
        tmp = "/tmp/_panel.png"
        cairosvg.svg2png(url=p(src), write_to=tmp, output_width=ww,
                         background_color=INK["GARMENT_WASHED_BLACK"]["hex"])
        img = Image.open(tmp).convert("RGBA")
        canvas = np.zeros((H, W, 4), dtype=np.uint8)
        canvas[py:py + img.height, px:px + img.width] = np.asarray(img, dtype=np.uint8)
        add(f"10_{name}", canvas)
        gd.rectangle([px, py, px + ww, py + hh], outline=(255, 0, 255, 210), width=2)
        gd.line([(px - 24, py), (px + 24, py)], fill=(0, 200, 255, 220), width=2)
        gd.line([(px, py - 24), (px, py + 24)], fill=(0, 200, 255, 220), width=2)
    add("90_GUIDES_print-bounds_do-not-print", np.asarray(guide))

    try:
        psd.save(out_path, compress=True)
    except TypeError:
        psd.save(out_path)
    return True


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #


def main() -> None:
    back_dark = p("design", "final", "final-back-print-on-dark.svg")
    back_light = p("design", "final", "final-back-print-on-light.svg")
    front_dark = p("design", "final", "final-front-chest-on-dark.svg")
    front_light = p("design", "final", "final-front-chest-on-light.svg")
    prime_dark = p("production", "svg", "final-back-print_on-dark_PRINTBUILD.svg")
    prime_light = p("production", "svg", "final-back-print_on-light_PRINTBUILD.svg")
    two_dark = p("production", "svg", "final-back-print_on-dark_2COLOR.svg")
    one_dark = p("production", "svg", "final-back-print_on-dark_1COLOR.svg")

    GARMENT_DARK = INK["GARMENT_WASHED_BLACK"]["hex"]
    GARMENT_LIGHT = INK["GARMENT_OFF_WHITE"]["hex"]
    jobs = [
        # (source svg, label, width, height, bands, gradient_map, garment bg or None)
        (back_dark, "back-print_on-dark_FULLCOLOR_dtg", 320, 400, 12, None, GARMENT_DARK),
        (back_light, "back-print_on-light_FULLCOLOR_dtg", 320, 400, 12, None, GARMENT_LIGHT),
        (prime_dark, "back-print_on-dark_PRINTBUILD", 320, 400, 2, None, GARMENT_DARK),
        (prime_light, "back-print_on-light_PRINTBUILD", 320, 400, 2, None, GARMENT_LIGHT),
        (two_dark, "back-print_on-dark_2COLOR", 320, 400, 0, None, GARMENT_DARK),
        (one_dark, "back-print_on-dark_1COLOR", 320, 400, 0, None, GARMENT_DARK),
        (front_dark, "front-chest_on-dark_PRINTBUILD", 90, 104, 2, None, GARMENT_DARK),
        (front_light, "front-chest_on-light_PRINTBUILD", 90, 104, 2, None, GARMENT_LIGHT),
    ]

    print("  (asset + manifest step is handled by tools/build_artwork.py)")

    # ---- spot (Pantone) print files: real PDF/EPS Separation plates ---------- #
    spot_jobs = [
        (prime_dark, "back-print_on-dark_SPOT-PANTONE", 320, 400),
        (prime_light, "back-print_on-light_SPOT-PANTONE", 320, 400),
        (two_dark, "back-print_on-dark_2COLOR_SPOT-PANTONE", 320, 400),
        (one_dark, "back-print_on-dark_1COLOR_SPOT-PANTONE", 320, 400),
        (p("production", "svg", "final-front-chest_on-dark_PRINTBUILD.svg"),
         "front-chest_on-dark_SPOT-PANTONE", 90, 104),
        (p("production", "svg", "final-front-chest_on-light_PRINTBUILD.svg"),
         "front-chest_on-light_SPOT-PANTONE", 90, 104),
        (p("production", "svg", "final-neck-label_on-dark_1COLOR.svg"),
         "neck-label_on-dark_SPOT-PANTONE", 64, 26),
        (p("production", "svg", "final-sleeve-mark_on-dark_1COLOR.svg"),
         "sleeve-mark_on-dark_SPOT-PANTONE", 44, 44),
    ]
    made: list[str] = []
    for src, label, wmm, hmm in spot_jobs:
        svg = read(src)
        name = f"superteamtr_{label}"
        pdf = p("production", "pdf-spot", name + ".pdf")
        eps = p("production", "eps-spot", name + ".eps")
        svg_to_pdf(svg, pdf, bands=1, spot=True, title=name)
        svg_to_eps(svg, eps, bands=1, spot=True, title=name)
        made += [pdf, eps]
        print("  ✓ spot", name)

    for src, label, wmm, hmm, bands, gmap, bg in jobs:
        svg = read(src)
        name = f"superteamtr_{label}"
        pdf = p("production", "pdf-cmyk", name + ".pdf")
        eps = p("production", "eps-cmyk", name + ".eps")
        # PDF -> review presentation (garment colour shown, like the real shirt)
        svg_to_pdf(svg, pdf, bands=bands or 1, gradient_flat_map=gmap,
                   page_bg=bg, title=name)
        # EPS -> production artwork, ink values only (no garment background)
        svg_to_eps(svg, eps, bands=bands or 1, gradient_flat_map=gmap, title=name)
        png = p("production", "png-300dpi", name + "_300dpi_transparent.png")
        rasterize(svg, png, wmm, hmm)
        made += [pdf, eps, png]
        print("  ✓", name)

    # -- separations from the print build (screen printing) ------------------- #
    svg = read(prime_dark)
    seps = [
        ("FILM-1_UNDERBASE_white-union", WHITE, True),
        ("FILM-2_TR-RED", RED, False),
        ("FILM-3_SOLANA-PURPLE", PURPLE, False),
        ("FILM-4_SOLANA-TEAL", TEAL, False),
    ]
    for name, colour, union in seps:
        out = p("production", "separations", f"superteamtr_back-print_on-dark_{name}.pdf")
        # union plate = every ink's shape (the white underbase is the union of all
        # four films); individual plates carry only their own shape
        svg_to_pdf(svg, out, bands=2, separate_fill=None if union else colour,
                   film=True, title=name)
        out_eps = p("production", "separations", f"superteamtr_back-print_on-dark_{name}.eps")
        svg_to_eps(svg, out_eps, bands=2, separate_fill=None if union else colour,
                   film=True, title=name)
        made += [out, out_eps]
        print("  ✓ separation", name)

    # two-ink separations (white + Solana green)
    svg2 = read(two_dark)
    for name, colour in (("2INK-FILM-1_base-white", WHITE), ("2INK-FILM-2_solana-green", GREEN)):
        out = p("production", "separations", f"superteamtr_back-print_2COLOR_{name}.pdf")
        svg_to_pdf(svg2, out, bands=1, separate_fill=colour, film=True, title=name)
        made.append(out)

    # one-colour film
    out = p("production", "separations", "superteamtr_back-print_1COLOR_white.pdf")
    svg_to_pdf(read(one_dark), out, bands=1, film=True, title="1 colour film")
    made.append(out)

    # -- CMYK soft proof TIFFs ------------------------------------------------ #
    for label, src in (("back-print_on-dark_PRINTBUILD", prime_dark),
                       ("back-print_on-light_PRINTBUILD", prime_light),
                       ("back-print_on-dark_FULLCOLOR_dtg", back_dark),
                       ("front-chest_on-dark_PRINTBUILD", front_dark)):
        png_in = p("production", "png-300dpi", f"superteamtr_{label}_300dpi_transparent.png")
        tif = p("production", "tiff-300dpi", f"superteamtr_{label}_300dpi_CMYK.tiff")
        if os.path.exists(png_in):
            to_cmyk_tiff(png_in, tif)
            made.append(tif)
            print("  ✓ CMYK proof", label)

    # -- layered PSD set ------------------------------------------------------ #
    psd_jobs = [
        ("superteamtr_back-print_on-dark_layered.psd", prime_dark, 320, 400,
         INK["GARMENT_WASHED_BLACK"]["hex"]),
        ("superteamtr_back-print_on-light_layered.psd", prime_light, 320, 400,
         INK["GARMENT_OFF_WHITE"]["hex"]),
        ("superteamtr_front-chest_on-dark_layered.psd",
         p("production", "svg", "final-front-chest_on-dark_PRINTBUILD.svg"), 90, 104,
         INK["GARMENT_WASHED_BLACK"]["hex"]),
        ("superteamtr_back-print_on-dark_FULLCOLOR_layered.psd", back_dark, 320, 400,
         INK["GARMENT_WASHED_BLACK"]["hex"]),
    ]
    for fname, src, wmm, hmm, garment in psd_jobs:
        psd_path = p("production", "psd", fname)
        if build_psd(src, psd_path, wmm, hmm, garment):
            made.append(psd_path)
            print("  ✓ layered PSD", fname)
    panels_psd = p("production", "psd", "superteamtr_all-panels_1to1_layered.psd")
    if build_panels_psd(panels_psd):
        made.append(panels_psd)
        print("  ✓ layered PSD superteamtr_all-panels_1to1_layered.psd")

    # -- palette documentation ----------------------------------------------- #
    palette = {k: v for k, v in INK.items()}
    for key, ink in palette.items():
        r, g, b = hex_to_rgb(ink["hex"])
        ink_doc = dict(ink)
        ink_doc["rgb"] = [r, g, b]
        ink_doc["hex"] = ink["hex"].upper()
        palette[key] = ink_doc
    with open(p("production", "colour-palette.json"), "w", encoding="utf-8") as fh:
        json.dump({"_note": "SuperteamTR T-shirt colour system - HEX/RGB/CMYK + Pantone "
                            "spot names. The *_SPOT-PANTONE.pdf/.eps files carry these "
                            "inks as real PDF/PS Separation colour spaces.",
                   "inks": palette,
                   "spot_ink_order": ["PANTONE White C (underbase)",
                                      "PANTONE 199 C",
                                      "PANTONE 2665 C",
                                      "PANTONE 338 C"],
                   "hero_separations": HERO_SEPARATIONS}, fh, indent=2)
    print("  ✓ colour-palette.json")

    print(f"\n{len(made)} production files written")


if __name__ == "__main__":
    main()
