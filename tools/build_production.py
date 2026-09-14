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
from PIL import Image                # noqa: E402

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


def build_psd(svg_text: str, out_path: str, width_mm: float, height_mm: float,
              garment: str, title: str) -> bool:
    try:
        from psd_tools import PSDImage
    except Exception as exc:  # pragma: no cover
        print("  ! psd-tools unavailable:", exc)
        return False

    dpi = 100          # layer resolution: plenty for a print-layer guide file
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

    # per-ink coverage layers
    for name, colour in (("01_INK_WHITE_underbase", WHITE), ("02_INK_TR_RED", RED),
                         ("03_INK_SOLANA_PURPLE", PURPLE), ("04_INK_SOLANA_GREEN", GREEN),
                         ("05_INK_SOLANA_TEAL", TEAL)):
        m = np.asarray(ink_mask(svg_text, colour, width_mm, height_mm, dpi), dtype=np.uint8)
        if m.max() == 0:
            continue
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        r, gch, b = hex_to_rgb(colour)
        rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2] = r, gch, b
        rgba[:, :, 3] = m
        add(name, rgba)

    # flattened master reference
    tmp = "/tmp/_master.png"
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=tmp,
                     output_width=w, background_color=None)
    master = np.asarray(Image.open(tmp).convert("RGBA"), dtype=np.uint8)
    add("06_MASTER_REFERENCE (do not print)", master, visible=False)

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

    made: list[str] = []
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

    # -- layered PSD ---------------------------------------------------------- #
    psd_path = p("production", "psd", "superteamtr_back-print_on-dark_layered.psd")
    if build_psd(read(prime_dark), psd_path, 320, 400,
                 INK["GARMENT_WASHED_BLACK"]["hex"], "SuperteamTR back print"):
        made.append(psd_path)
        print("  ✓ layered PSD")

    # -- palette documentation ----------------------------------------------- #
    palette = {k: v for k, v in INK.items()}
    for key, ink in palette.items():
        r, g, b = hex_to_rgb(ink["hex"])
        ink_doc = dict(ink)
        ink_doc["rgb"] = [r, g, b]
        ink_doc["hex"] = ink["hex"].upper()
        palette[key] = ink_doc
    with open(p("production", "colour-palette.json"), "w", encoding="utf-8") as fh:
        json.dump({"_note": "SuperteamTR T-shirt colour system - HEX/RGB/CMYK + nearest Pantone",
                   "inks": palette,
                   "hero_separations": HERO_SEPARATIONS}, fh, indent=2)
    print("  ✓ colour-palette.json")

    print(f"\n{len(made)} production files written")


if __name__ == "__main__":
    main()
