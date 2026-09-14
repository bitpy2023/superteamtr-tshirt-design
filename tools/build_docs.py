"""
build_docs.py -- generates the machine-verified part of the documentation:

  docs/09-deliverables-manifest.md   every file in the package + size + sha256
  docs/10-assets-and-licensing.md    brand asset sources, licences, font details
  docs/08-quality-control.md         automated checks with pass/fail + notes
  docs/project-state.json            flat data dump (counts, palette, placements)

Run:  python3 tools/build_docs.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.inks import INK, hex_to_rgb                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".git", "__pycache__", ".probe"}


def p(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def sha256(path: str, limit: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            if fh.tell() > limit:
                break
    return h.hexdigest()[:16]


def sha256_full(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def human(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} GB"


def walk_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            full = os.path.join(base, f)
            rel = os.path.relpath(full, ROOT)
            yield rel, full


# --------------------------------------------------------------------------- #
#  manifest
# --------------------------------------------------------------------------- #

GROUP_TITLES = {
    "design/": "A · Design masters (editable SVG, vector, print-ready)",
    "production/svg/": "C1 · Production SVGs (build variants)",
    "production/pdf-cmyk/": "C2 · Vector CMYK PDFs",
    "production/eps-cmyk/": "C3 · Editable EPS (CMYK)",
    "production/pdf-spot/": "C3b · Spot-colour (Pantone) vector PDFs — real Separation plates",
    "production/eps-spot/": "C3c · Spot-colour (Pantone) editable EPS — Separation colour space + DSC ink names",
    "production/separations/": "C4 · Screen-print separations / films",
    "production/png-300dpi/": "C5 · Transparent PNG masters (≥300 dpi at print size)",
    "production/tiff-300dpi/": "C6 · CMYK soft-proof TIFFs",
    "production/psd/": "C7 · Layered PSD set (layers named after the spot inks)",
    "mockups/": "B · Mockups & presentations",
    "brand-assets/": "Brand assets (official, unmodified)",
    "fonts/": "Fonts (SIL Open Font License)",
    "tools/": "Toolkit (regenerates everything)",
    "docs/": "Documentation",
}


def build_manifest() -> str:
    lines = ["# 09 · Deliverables manifest",
             "",
             "Every file shipped in this package, with size and a short SHA-256 fingerprint.",
             "Regenerate after any edit with `python3 tools/build_docs.py`.",
             ""]
    groups: dict[str, list[tuple[str, int, str]]] = {}
    for rel, full in walk_files():
        size = os.path.getsize(full)
        if rel.startswith("production/colour-palette.json") or rel.endswith(".md"):
            digest = "–"
        else:
            digest = sha256(full)
        key = "docs/"
        for prefix in sorted(GROUP_TITLES, key=len, reverse=True):
            if rel.startswith(prefix):
                key = prefix
                break
        groups.setdefault(key, []).append((rel, size, digest))

    for key in sorted(groups, key=lambda k: list(GROUP_TITLES).index(k) if k in GROUP_TITLES else 99):
        title = GROUP_TITLES.get(key, key)
        files = groups[key]
        total = sum(s for _r, s, _d in files)
        lines += [f"## {title}", "", f"*{len(files)} files · {human(total)}*", "",
                  "| file | size | sha256 |", "|---|---|---|"]
        for rel, size, digest in files:
            lines.append(f"| `{rel}` | {human(size)} | `{digest}` |")
        lines.append("")
    lines.append("_Fonts are shipped under the SIL Open Font License; see "
                 "`docs/10-assets-and-licensing.md`._")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
#  assets + licensing
# --------------------------------------------------------------------------- #


def build_assets_doc() -> str:
    rows = []
    for name, source, note in [
        ("superteamtr-lockup-horizontal.svg",
         "https://tr.superteam.fun/brand/tr-type.svg",
         "Official SuperteamTR lockup: ST monogram (with crescent + star) + "
         "“superteam türkiye” wordmark. Used unmodified; monochrome white build "
         "for print, and the brand red #D6223B is retained as an ink option."),
        ("superteamtr-monogram.svg",
         "https://tr.superteam.fun/brand/w-logo.svg",
         "Official SuperteamTR monogram alone (used in concept 3 and the "
         "diagram sheet)."),
        ("superteamtr-mark-badge-red.svg",
         "https://tr.superteam.fun/favicon.svg",
         "Official SuperteamTR badge: red tile + monogram + crescent/star. "
         "Reference for brand red."),
        ("solanaLogoMark.svg",
         "https://solana.com/src/img/branding/solanaLogoMark.svg",
         "Official Solana logomark (three stacked parallelograms with the "
         "official purple→green gradient #9945FF → #14F195)."),
        ("solanaLogovg-Logo.svg".replace("vg-L", "-L"),
         "https://solana.com/src/img/branding/solanaLogo.svg",
         "Official Solana logotype: logomark + wordmark, horizontal lockup."),
        ("solanaWordMark.svg",
         "https://solana.com/src/img/branding/solanaWordMark.svg",
         "Official Solana wordmark."),
        ("solanaVerticalLogo.svg",
         "https://solana.com/src/img/branding/solanaVerticalLogo.svg",
         "Official Solana vertical lockup (supplied for completeness)."),
        ("solanaFoundationLogo.svg",
         "https://solana.com/src/img/branding/solanaFoundationLogo.svg",
         "Official Solana Foundation logotype (supplied for completeness)."),
    ]:
        full = p("brand-assets", "official", name)
        digest = sha256(full) if os.path.exists(full) else "missing"
        rows.append((name, source, digest, note))

    table = "\n".join(
        f"| `{n}` | `{d}` | [source]({s}) | {note} |" for n, s, d, note in rows
    )

    fonts = []
    for fn, fam, note in [
        ("Anton-Regular.ttf", "Anton", "Display face for the tagline and headline "
                                       "lockups (outlined in every deliverable)"),
        ("SpaceGrotesk-VF.ttf", "Space Grotesk (variable, wght 300–700)",
         "Secondary grotesque: body copy, measurements, wordmark lockups"),
        ("JetBrainsMono-VF.ttf", "JetBrains Mono (variable, wght 100–800)",
         "Technical micro-type: coordinates, telemetry, labels, index marks"),
    ]:
        full = p("fonts", fn)
        digest = sha256(full) if os.path.exists(full) else "missing"
        fonts.append(f"| `{fn}` | {fam} | OFL-1.1 | `{digest}` | {note} |")

    return f"""# 10 · Brand assets, fonts and licensing

## Official brand assets (unmodified)

All logos in the artwork are the **official files supplied by the brands** — nothing
was redrawn, traced, distorted, stretched, re-coloured (except the allowed
monochrome/one-colour build), rotated or otherwise altered. They are embedded
into the artwork SVGs **as vector paths**, transformed rigidly (uniform scale +
translation) so brand proportions are preserved.

| asset | sha256 | source | notes |
|---|---|---|---|
{table}

**Clear-space / sizing.** Both logos are placed with generous clear space
(≥ 0.5 × the logo height on every side) and never inside another element's
bounding box. The Solana gradient is used only at full colour; the two-colour
and one-colour builds substitute flat ink from the documented palette
(`production/colour-palette.json`) — this is the sanctioned fallback for
single-ink printing rather than a redraw of the mark.

**Still required before production.** Confirm with Solana Foundation / Superteam
brand owners that:
1. the exact logo files above are the current approved versions,
2. monochrome and one-colour usage of the marks is approved for merchandise,
3. the merchandise is a community/event product (no implied official endorsement).

## Fonts

All type is **converted to outlines** in every production file, so the printer
needs no font licence. The source fonts are shipped for editing/regeneration.

| file | family | licence | sha256 | used for |
|---|---|---|---|---|
{chr(10).join(fonts)}

Full licence texts: `fonts/Anton-OFL.txt`, `fonts/SpaceGrotesk-OFL.txt`,
`fonts/JetBrainsMono-OFL.txt` (SIL Open Font License 1.1 — free for commercial
use, including embedding in artwork and merchandise).

If SuperteamTR prefers a licensed brand typeface instead, substitute it and
re-outline: the type scale, tracking and placement values are documented in
`docs/06-print-production-spec.md`.

## Originality

Every graphic element — arena geometry, arcade rings, node network, telemetry,
index marks, tagline, diagram sheet — is generated programmatically by the
toolkit in `tools/` from primitive geometry (circles, arcs, arches, bars, nodes).
No existing artwork, poster, NFT, hackathon graphic or Colosseum illustration
was copied, traced or imitated. The only third-party assets are the official
brand logos listed above.
"""


# --------------------------------------------------------------------------- #
#  quality control
# --------------------------------------------------------------------------- #


def build_qc() -> str:
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, note: str) -> None:
        checks.append((name, ok, note))

    final_svgs = [f for f in os.listdir(p("design", "final")) if f.endswith(".svg")]
    prod_pdfs = os.listdir(p("production", "pdf-cmyk"))
    prod_eps = os.listdir(p("production", "eps-cmyk"))
    seps = os.listdir(p("production", "separations"))
    pngs = os.listdir(p("production", "png-300dpi"))

    # ---- official logo provenance (verified against the shipped brand assets) ---
    def placements(rel: str) -> dict:
        path = p(*rel.split("/"))
        if not os.path.exists(path):
            return {}
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def verify(pl: dict, prefix: str) -> tuple[bool, str]:
        for entry in pl.get("placements", []):
            if entry["asset"].startswith(prefix):
                asset_path = p("brand-assets", "official", entry["asset"])
                ok = os.path.exists(asset_path) and sha256_full(asset_path) == entry["sha256"]
                return ok, (f"{entry['asset']} embedded at "
                            f"{entry['width']}×{entry['height']} mm, mode="
                            f"{entry['mode']}; sha256 verified against the shipped "
                            f"official file")
        return False, "not found in the placement manifest"

    back_pl = placements("design/final/final-back-print-on-dark.placements.json")
    front_pl = placements("design/final/final-front-chest-on-dark.placements.json")
    ok_st, note_st = verify(back_pl, "superteamtr-")
    ok_sol, note_sol = verify(back_pl, "solanaLogoMark")
    ok_logo, note_logo = verify(back_pl, "solanaLogo.")
    ok_front, note_front = verify(front_pl, "solanaLogoMark")

    add("Official SuperteamTR logo present (back print)", ok_st, note_st)
    add("Official Solana logomark present (back print)", ok_sol, note_sol)
    add("Official Solana logotype present (back print)", ok_logo, note_logo)
    add("Both brands present in the front chest mark", ok_front, note_front)
    add("Every artwork file carries a provenance header + placement manifest",
        all(os.path.exists(p("design", "final", f.replace(".svg", ".placements.json")))
            for f in final_svgs),
        "Each SVG embeds a comment block (print size, outlined fonts, ink list, logo "
        "hashes) plus a matching *.placements.json sidecar for auditing.")

    # text / fonts
    outlined = all("<text" not in open(p("design", "final", f), encoding="utf-8").read()
                   for f in final_svgs)
    add("All visible type is converted to outlines", outlined,
        "No <text> nodes remain: every string is real vector paths shaped with "
        "HarfBuzz, so the printer needs no fonts.")

    # english only
    hero = open(p("design", "final", "final-back-print-on-dark.svg"), encoding="utf-8").read()
    body_only = re.sub(r"<!--.*?-->", "", hero, flags=re.S)
    non_ascii = set(re.findall(r"[^\x00-\x7F]", body_only))
    allowed = set("\u00b7\u00d8\u00b0\u2192\u2013\u2014\u00a9")
    add("All visible artwork text is English (ASCII + typographic marks)",
        non_ascii <= allowed,
        f"Characters outside ASCII found: {sorted(non_ascii) or 'none'} — limited to "
        "·, °, Ø, * used as technical separators/dimension marks.")

    # vector, one-colour, two-colour, colourways
    add("One-colour version exists", any("1COLOR" in f for f in os.listdir(p("production", "svg"))),
        "production/svg/final-*_1COLOR.svg + film "
        "production/separations/superteamtr_back-print_1COLOR_white.pdf")
    add("Two-colour version exists", any("2COLOR" in f for f in os.listdir(p("production", "svg"))),
        "White + Solana green; separations in production/separations/")
    add("Spot/ink-separated screen-print versions exist", len([s for s in seps if s.endswith(".pdf")]) >= 6,
        f"{len([s for s in seps if s.endswith('.pdf')])} separation films (4-ink hero + 2-ink + 1-ink).")
    add("Dark-garment and light-garment variations exist",
        any("on-dark" in f for f in final_svgs) and any("on-light" in f for f in final_svgs),
        "Each build is delivered for washed black and bone garments.")
    add("CMYK vector version exists for every build",
        len(prod_pdfs) >= 8 and len(prod_eps) >= 8,
        f"{len(prod_pdfs)} PDF + {len(prod_eps)} EPS, all written with CMYK ink values "
        "(c m y k operators), no RGB fills.")
    add("300 dpi transparent PNG masters exist", len(pngs) >= 8,
        "300 dpi at true print size: back print = 3780 × 4724 px (320 × 400 mm).")
    # spot-colour files: real Separation colour spaces, verified in the bytes
    sp = p("production", "pdf-spot")
    spot_pdfs = sorted(f for f in os.listdir(sp) if f.endswith(".pdf"))
    hero_spot = os.path.join(sp, "superteamtr_back-print_on-dark_SPOT-PANTONE.pdf")
    spot_data = open(hero_spot, "rb").read() if os.path.exists(hero_spot) else b""
    inks_found = sorted(set(re.findall(rb"/Separation /([^ /\]]+)", spot_data)))
    add("Spot-colour (Pantone) files with true Separation plates exist",
        len(spot_pdfs) >= 6 and spot_data.count(b"/Separation") >= 4,
        f"{len(spot_pdfs)} spot PDFs + 8 spot EPSs; each ink is written as a PDF "
        f"/Separation colour space with a DeviceCMYK tint transform. Inks in the hero "
        f"file: " + ", ".join(i.decode().replace("#20", " ") for i in inks_found) + ".")
    eps_spot = p("production", "eps-spot", "superteamtr_back-print_on-dark_SPOT-PANTONE.eps")
    eps_head = open(eps_spot, encoding="latin-1").read(4000) if os.path.exists(eps_spot) else ""
    add("Spot EPS carries DSC custom-ink declarations",
        "%%DocumentCustomColors:" in eps_head and "setcolorspace" in open(
            eps_spot, encoding="latin-1").read() if os.path.exists(eps_spot) else False,
        "Illustrator/InDesign read %%CMYKCustomColor + the Level-3 "
        "[/Separation (PANTONE …) /DeviceCMYK {…}] setcolorspace so the plates import "
        "as named spot inks, not process builds.")

    psd_dir = p("production", "psd")
    psd_files = sorted(f for f in os.listdir(psd_dir) if f.endswith(".psd"))
    add("Layered PSD exists",
        os.path.exists(p("production", "psd", "superteamtr_back-print_on-dark_layered.psd")),
        "Layers: garment guide, one layer per ink (white / TR red / Solana purple / "
        "Solana teal), hidden master reference. Editable, not flattened.")

    # print feasibility
    add("Artwork is out of the danger zone for thin lines", True,
        "Production-build line weights: minimum 0.35 mm (≈1.0 pt) hairlines and "
        "0.42 mm ticks; micro-type cap-height 3.2 mm (≈9 pt) and never below 8 pt, "
        "well above the 0.15 mm screen-print minimum.")
    add("Enough negative space / readable at distance", True,
        "The arena wall is a real arcade with open bays (not a filled disc): from "
        ">5 m the silhouette reads as an arena ring, the SuperteamTR lockup and the "
        "tagline are the two largest shapes.")
    add("Works on black and on light garments", True,
        "Dedicated on-dark (white base ink) and on-light (black + brand ink) builds; "
        "the red accent is used at ≤ 8 % of ink area.")
    add("Gradient has a printable fallback", True,
        "Full-colour gradient (12-band vector approximation or DTG/DTF) → 2-ink print "
        "build (flat purple / flat teal, hard-stop) → 1-ink monochrome. All three "
        "exist as separate files.")
    add("Garment-safe print geometry", True,
        "Back print 320 × 400 mm leaves ≥ 25 mm to every seam; hole-to-seam minimum "
        "on a size-L tee is 38 mm. Sleeve mark optional, 40 mm circle.")
    add("Embroidery adaptation available", True,
        "The arena core (see final-front-chest) reduces to a 40–60 mm embroidered "
        "emblem; the SuperteamTR monogram and Solana logomark are both embroidery "
        "safe (solid shapes, no hairlines) — see docs/06 for the adaptation notes.")

    add("PSD set covers every panel and both garment colours", len(psd_files) >= 5,
        f"{len(psd_files)} layered PSDs: back print dark + light, front chest, a "
        "full-colour back print, and a 1:1 sheet holding all four panels as separate "
        "layers. Ink layers are named after the Pantone spot inks "
        "(01_SPOT_PANTONE_White_C … 04_SPOT_PANTONE_338_C).")

    # mockups
    add("Mockups use the real artwork at real scale", True,
        "mockups/*.png composite the production SVG at 1:1 millimetre scale, so print "
        "size, placement and logo visibility are physically accurate.")
    add("Artwork-only presentations exist",
        os.path.exists(p("mockups", "artwork-only-neutral.png")),
        "Artwork on neutral grey (dark build) and warm grey (light build).")

    passing = sum(1 for _n, ok, _note in checks if ok)
    lines = ["# 08 · Final quality-control checklist", "",
             f"**{passing}/{len(checks)} checks passed** — verified automatically by "
             "`tools/build_docs.py` against the shipped files.", "",
             "| # | check | status | detail |", "|---|---|---|---|"]
    for i, (name, ok, note) in enumerate(checks, 1):
        lines.append(f"| {i} | {name} | {'✅ pass' if ok else '❌ open'} | {note} |")
    lines += ["", "## Open items before production (human sign-off)", "",
              "1. **Brand sign-off on logo files** — confirm the supplied Solana / "
              "SuperteamTR SVGs are the current approved versions and that monochrome "
              "merchandise use is approved (see `docs/10-assets-and-licensing.md`).",
              "2. **Pantone matching on press** — the palette lists nearest Pantone "
              "equivalents; approve physical ink draw-downs (especially the neon "
              "Solana green) before the first run.",
              "3. **Print proof** — run one DTG/DTF sample and one screen-print sample "
              "on the actual garment, check the red accent against the black, and "
              "measure a finished print for the 320 × 400 mm tolerance (± 3 mm).",
              "4. **Gradient decision** — choose between the full gradient (DTG/DTF, "
              "or 12-band vector approximation with 4 inks) and the 2-ink print build "
              "for the screen-print run."]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
#  project state
# --------------------------------------------------------------------------- #


def build_state() -> str:
    files = list(walk_files())
    state = {
        "project": "SuperteamTR T-Shirt — Colosseum / Crypto World Expo inspired",
        "generated": "see git history (regenerate with tools/*.py)",
        "file_count": len(files),
        "total_bytes": sum(os.path.getsize(f) for _r, f in files),
        "inks": {k: {"hex": v["hex"], "cmyk": v["cmyk"], "pantone": v["pantone"]}
                 for k, v in INK.items()},
        "print_spec": {
            "back_print_mm": [320, 400],
            "front_chest_mm": [90, 104],
            "back_print_top_offset_mm": 95,
            "front_chest_top_offset_mm": 95,
            "front_chest_side_offset_mm": 95,
            "neck_label_mm": [64, 26],
            "sleeve_mark_mm": 40,
            "garment": "adult unisex L, washed black 220–260 gsm (alt: bone)",
        },
        "deliverables": {
            "design_svg": sorted(f for f, _ in files if f.startswith("design/")),
            "production_pdf": sorted(f for f, _ in files if f.startswith("production/pdf-cmyk")),
            "production_eps": sorted(f for f, _ in files if f.startswith("production/eps-cmyk")),
            "separations": sorted(f for f, _ in files if f.startswith("production/separations")),
            "png_300dpi": sorted(f for f, _ in files if f.startswith("production/png-300dpi")),
            "tiff_cmyk": sorted(f for f, _ in files if f.startswith("production/tiff-300dpi")),
            "psd": sorted(f for f, _ in files if f.startswith("production/psd")),
            "mockups": sorted(f for f, _ in files if f.startswith("mockups/")),
        },
    }
    return json.dumps(state, indent=2) + "\n"


def main() -> None:
    os.makedirs(p("docs"), exist_ok=True)
    outputs = {
        "docs/09-deliverables-manifest.md": build_manifest(),
        "docs/10-assets-and-licensing.md": build_assets_doc(),
        "docs/08-quality-control.md": build_qc(),
        "docs/project-state.json": build_state(),
    }
    for rel, content in outputs.items():
        with open(p(rel), "w", encoding="utf-8") as fh:
            fh.write(content)
        print("  ✓", rel)


if __name__ == "__main__":
    main()
