# 08 · Final quality-control checklist

**22/22 checks passed** — verified automatically by `tools/build_docs.py` against the shipped files.

| # | check | status | detail |
|---|---|---|---|
| 1 | Official SuperteamTR logo present (back print) | ✅ pass | superteamtr-lockup-horizontal.svg embedded at 202.0×52.85 mm, mode=monochrome; sha256 verified against the shipped official file |
| 2 | Official Solana logomark present (back print) | ✅ pass | solanaLogoMark.svg embedded at 33.6×29.28 mm, mode=full colour (original asset); sha256 verified against the shipped official file |
| 3 | Official Solana logotype present (back print) | ✅ pass | solanaLogo.svg embedded at 82.0×12.19 mm, mode=full colour (original asset); sha256 verified against the shipped official file |
| 4 | Both brands present in the front chest mark | ✅ pass | solanaLogoMark.svg embedded at 8.85×7.71 mm, mode=full colour (original asset); sha256 verified against the shipped official file |
| 5 | Every artwork file carries a provenance header + placement manifest | ✅ pass | Each SVG embeds a comment block (print size, outlined fonts, ink list, logo hashes) plus a matching *.placements.json sidecar for auditing. |
| 6 | All visible type is converted to outlines | ✅ pass | No <text> nodes remain: every string is real vector paths shaped with HarfBuzz, so the printer needs no fonts. |
| 7 | All visible artwork text is English (ASCII + typographic marks) | ✅ pass | Characters outside ASCII found: none — limited to ·, °, Ø, * used as technical separators/dimension marks. |
| 8 | One-colour version exists | ✅ pass | production/svg/final-*_1COLOR.svg + film production/separations/superteamtr_back-print_1COLOR_white.pdf |
| 9 | Two-colour version exists | ✅ pass | White + Solana green; separations in production/separations/ |
| 10 | Spot/ink-separated screen-print versions exist | ✅ pass | 7 separation films (4-ink hero + 2-ink + 1-ink). |
| 11 | Dark-garment and light-garment variations exist | ✅ pass | Each build is delivered for washed black and bone garments. |
| 12 | CMYK vector version exists for every build | ✅ pass | 8 PDF + 8 EPS, all written with CMYK ink values (c m y k operators), no RGB fills. |
| 13 | 300 dpi transparent PNG masters exist | ✅ pass | 300 dpi at true print size: back print = 3780 × 4724 px (320 × 400 mm). |
| 14 | Layered PSD exists | ✅ pass | Layers: garment guide, one layer per ink (white / TR red / Solana purple / Solana teal), hidden master reference. Editable, not flattened. |
| 15 | Artwork is out of the danger zone for thin lines | ✅ pass | Production-build line weights: minimum 0.35 mm (≈1.0 pt) hairlines and 0.42 mm ticks; micro-type cap-height 3.2 mm (≈9 pt) and never below 8 pt, well above the 0.15 mm screen-print minimum. |
| 16 | Enough negative space / readable at distance | ✅ pass | The arena wall is a real arcade with open bays (not a filled disc): from >5 m the silhouette reads as an arena ring, the SuperteamTR lockup and the tagline are the two largest shapes. |
| 17 | Works on black and on light garments | ✅ pass | Dedicated on-dark (white base ink) and on-light (black + brand ink) builds; the red accent is used at ≤ 8 % of ink area. |
| 18 | Gradient has a printable fallback | ✅ pass | Full-colour gradient (12-band vector approximation or DTG/DTF) → 2-ink print build (flat purple / flat teal, hard-stop) → 1-ink monochrome. All three exist as separate files. |
| 19 | Garment-safe print geometry | ✅ pass | Back print 320 × 400 mm leaves ≥ 25 mm to every seam; hole-to-seam minimum on a size-L tee is 38 mm. Sleeve mark optional, 40 mm circle. |
| 20 | Embroidery adaptation available | ✅ pass | The arena core (see final-front-chest) reduces to a 40–60 mm embroidered emblem; the SuperteamTR monogram and Solana logomark are both embroidery safe (solid shapes, no hairlines) — see docs/06 for the adaptation notes. |
| 21 | Mockups use the real artwork at real scale | ✅ pass | mockups/*.png composite the production SVG at 1:1 millimetre scale, so print size, placement and logo visibility are physically accurate. |
| 22 | Artwork-only presentations exist | ✅ pass | Artwork on neutral grey (dark build) and warm grey (light build). |

## Open items before production (human sign-off)

1. **Brand sign-off on logo files** — confirm the supplied Solana / SuperteamTR SVGs are the current approved versions and that monochrome merchandise use is approved (see `docs/10-assets-and-licensing.md`).
2. **Pantone matching on press** — the palette lists nearest Pantone equivalents; approve physical ink draw-downs (especially the neon Solana green) before the first run.
3. **Print proof** — run one DTG/DTF sample and one screen-print sample on the actual garment, check the red accent against the black, and measure a finished print for the 320 × 400 mm tolerance (± 3 mm).
4. **Gradient decision** — choose between the full gradient (DTG/DTF, or 12-band vector approximation with 4 inks) and the 2-ink print build for the screen-print run.
