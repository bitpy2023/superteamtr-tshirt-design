# 06 · Typography, colour, composition and print-production specification

This is the document a print shop needs. Everything below matches the shipped
files exactly; the artwork files regenerate from `tools/` if anything changes.

---

## 1. Typography system

All type is **converted to outlines** in every deliverable (no fonts required by
the printer). Source fonts ship under the SIL Open Font License.

| Role | Typeface | Weight | Case | Tracking | Size (back print) |
|---|---|---|---|---|---|
| Tagline `THE ARENA FOR BUILDERS` | **Anton** (display) | 400 | CAPS | +9 % | cap height 21.8 mm (≈ 52 pt) |
| Wordmark `SuperteamTR` | **Space Grotesk** | 700 | Title | +6 % | cap height 10.0 mm (≈ 24 pt) |
| Header / data row | **JetBrains Mono** | 500 | CAPS | +34 % | cap height 3.4 mm (≈ 9 pt) |
| Footer `CONNECT. CREATE. SHIP.` | **JetBrains Mono** | 500 | CAPS | +42 % | cap height 3.0 mm (≈ 8.5 pt) |
| Micro specs / title block | **JetBrains Mono** | 500 | CAPS + Title | +16…22 % | cap height 2.2 mm (≈ 8 pt) minimum |

**Minimum readable sizes used:** 8 pt on the back print (title block) and 4.4 mm
cap height on the sleeve mark (≈ 11 pt). Nothing in any production build is
smaller than 8 pt / 0.35 mm line weight.

**Type rules**
* English only; no decorative fonts; no fake technical text — every label is a
  real value (coordinates, counts, tier data, print specs).
* Headline and tagline are single-line, centred, optically tracked.
* Circular type (concept 3 only) sits on true circles, one rotation per glyph.

If SuperteamTR licenses a brand typeface later: replace the three families in
`tools/build_artwork.py::shaper()`, rebuild, and the outlines update; keep the
sizes/tracking from the table above.

---

## 2. Colour system

`production/colour-palette.json` carries the same data in machine-readable form.

### Inks

| Ink | HEX | RGB | CMYK (build) | Pantone (nearest) | Where used |
|---|---|---|---|---|---|
| White (base) | `#FFFFFF` | 255,255,255 | 0/0/0/0 | *opaque white plastisol / DTG underbase* | all line work, type, arcs on dark garments |
| SuperteamTR red | `#D6223B` | 214,34,59 | 6/95/72/0 | **199 C** | gate keystones, bridge nodes, index marks, gradient ring (≤ 8 % of ink area) |
| Solana purple | `#9945FF` | 153,69,255 | 68/79/0/0 | **2665 C** | Solana logomark gradient start, logotype |
| Solana teal | `#28E0B9` | 40,224,185 | 52/0/38/0 | **338 C** | mid step of the gradient; second ink in the 2-colour build |
| Solana green | `#14F195` | 20,241,149 | 55/0/60/0 | **802 C / 3385 C** | Solana logomark gradient end (gradient builds only) |
| Blueprint black | `#0B0B10` | 11,11,16 | 60/55/55/100 | Black 6 C | concept 2 line work, all "on-light" builds |

### Garments

| Garment | HEX | CMYK reference | Role |
|---|---|---|---|
| Washed black | `#17171A` | 65/60/55/95 | primary garment for the hero build |
| Bone / natural | `#E9E4D8` | 6/6/14/0 | alternative garment (light build + concept 2) |
| Charcoal | `#2B2B2F` | 60/52/48/72 | optional third colourway |

### Gradient policy

The Solana logomark **must** keep its official purple→green gradient in the
primary digital build. Print builds:

1. **DTG / DTF** — gradient as supplied (12-band vector approximation in the PDF).
2. **Screen print, 4 inks** — hard-stop two-band inside the logomark
   (purple top band / teal bottom band). Files:
   `production/svg/…_PRINTBUILD.svg`, separations in `production/separations/`.
3. **2 inks** — logomark becomes flat Solana green.
4. **1 ink** — whole artwork monochrome (white on dark, black on light).

Never print the gradient as a photorealistic/continuous-tone fade on press, and
never substitute a different green/purple: use the table above.

---

## 3. Composition & placement

### Back print (hero) — Fig. A
* Size **320 × 400 mm** (12.6 × 15.7 in), vector, aspect ratio 4:5.
* Centred on the body, **95 mm below the neck rib** (≈ 20 mm below the yoke seam).
* Print area check on a size-L tee (520 × 720 mm flat): 25 mm minimum clearance
  to every seam, 38 mm minimum at the closest point.
* Element hierarchy: arena emblem (Ø 224 mm) → SuperteamTR lockup → tagline →
  Solana logotype → data rows.

### Front chest mark — Fig. B
* Size **90 × 104 mm**, **95 mm below the shoulder seam**, **95 mm from the
  centre line** (wearer's right chest), 4:5 aspect.
* Contains: arena emblem (compact build), `SUPERTEAMTR`, `Solana Ecosystem`.

### Neck label — Fig. C
* **64 × 26 mm**, printed/heat-transferred inside the back neck, 20 mm below the
  collar seam. Red tick + `SuperteamTR` + `Solana Ecosystem · Istanbul` +
  official Solana logotype.

### Sleeve mark (optional) — Fig. D
* **40 mm circle**, 60 mm below the sleeve seam on the left sleeve, outer face.

### Composition rules
* No element crosses a seam, a side fold or the neck rib.
* Negative space is never filled: the arena's bays are true openings.
* At 5 m the shirt should read: *arena · superteam türkiye · THE ARENA FOR
  BUILDERS* — in that order.

---

## 4. Mockups (what was delivered and how to re-shoot)

| File | Shows |
|---|---|
| `mockup-back-view.png` | dark garment, full back print, shadowed studio render |
| `mockup-front-view.png` | dark garment, front chest placement |
| `mockup-dark-garment.png` | dark garment, print-scale reference |
| `mockup-light-garment.png` | bone garment with the light build |
| `mockup-flatlay-back.png` / `mockup-flatlay-dark.png` | flat-lay, slight rotation, fabric grain |
| `mockup-detail-closeup.png` | 110 × 62 mm of the print at 2× (print-quality inspection) |
| `mockup-print-placement.png` | technical placement sheet with all measurements |
| `artwork-only-neutral.png` / `artwork-only-light.png` | artwork only, neutral backgrounds |

These are generated renders that composite the **actual production file at
1:1 millimetre scale**, so print size, placement and logo visibility are
physically accurate. For marketing photography, shoot a real blank to these
numbers: back print top edge at 95 mm below the collar seam, 320 mm wide.

---

## 5. Print-production specification

### Screen printing (recommended for runs ≥ 50)
* Mesh: 160–200 t/in (white underbase 110–125 t), 55–70 shore squeegee, flash
  between the underbase and colours.
* Order: underbase (white, reduced/soft-hand) → TR red → Solana purple →
  Solana teal. Registration tolerance ± 0.5 mm.
* Plastisol or water-based; soft-hand additive on the underbase for the dark
  garment. Cure 160 °C / 320 °F, 60–90 s.
* The white underbase film is the **union plate** (all four inks) plus a 1.5 mm
  trap — file: `…_FILM-1_UNDERBASE_white-union.pdf`.
* Gradients: not on press — use the hard-stop two-band build.

### DTG (recommended for runs ≤ 50 / on-demand)
* 300 dpi minimum at print size; our PNG masters are 3780 × 4724 px for the back
  print (300 dpi at 320 × 400 mm).
* Pretreat dark garments, white underbase, then the colour pass.
* Wash test: 40 °C, 5 cycles, expect ≤ 5 % loss.

### DTF / transfer
* Mirror-print the PNG master, powder-cure, press 150–165 °C, 10–15 s, medium
  pressure; peel cold. Gradient and fine 0.35 mm lines both reproduce.

### Embroidery adaptation
* Use the arena core alone at 40–60 mm (derived from `final-front-chest`).
* Minimum stitchable detail is 0.8 mm — drop the telemetry ticks and the tick
  ring, keep the two arcades, the coin ring, the Solana logomark and the
  SuperteamTR monogram.
* Underlay: 2–3 mm edge walk; 40 wt polyester thread; digitise the Solana
  gradient as a two-colour satin split (purple / green), never a gradient fill.

### Vinyl / laser / stickers
* 1-colour SVG (`production/svg/final-*_1COLOR.svg`) is the cut-file source;
  minimum bridge width 1 mm, weed-friendly at 40 mm and larger.

### Spot colour (Pantone) plates — the preferred press setup

For screen printing the artwork is delivered as **real spot-colour files**, not
CMYK process builds:

| File set | Ink plates (named in the file) |
|---|---|
| `production/pdf-spot/superteamtr_back-print_on-dark_SPOT-PANTONE.pdf` | PANTONE White C (underbase) · PANTONE 199 C · PANTONE 2665 C · PANTONE 338 C |
| `production/eps-spot/…_SPOT-PANTONE.eps` | same, as PostScript Level-3 `[/Separation (PANTONE …) /DeviceCMYK {…}] setcolorspace` with `%%CMYKCustomColor` declarations |
| `…_2COLOR_SPOT-PANTONE.*` | PANTONE White C + PANTONE 802 C |
| `…_1COLOR_SPOT-PANTONE.*` | single ink (white on dark / PANTONE Black 6 C on light) |

Each plate is a true **Separation colour space** with a linear DeviceCMYK
alternate, so Illustrator / InDesign / the RIP list the inks by Pantone name,
generate one film per ink, and let the printer swap in the physical ink without
re-separating anything. If you would rather print process CMYK, the parallel
`pdf-cmyk/` and `eps-cmyk/` sets carry the documented CMYK builds of the same
artwork.

**Matching rule:** match to the Pantone references above on press — never to the
on-screen RGB values. Approve a draw-down for `PANTONE 802 C` (neon green) and
`199 C` (the SuperteamTR red) before the run; those two inks are the ones that
shift most between ink systems.

### Colour management
* The PDFs/EPSs write real CMYK ink values (`c m y k` operators) with the builds
  in §2; the TIFFs are naive soft proofs.
* Re-separate with the printer's ICC profile (e.g. Coated FOGRA39 for paper
  proofs, or the RIP's own profile for garment).
* Spot inks: match to the Pantone references in §2, not to screen RGB.

---

## 6. Which file to send to whom

| Supplier | Send |
|---|---|
| Screen printer | `production/separations/*.pdf` + `production/eps-cmyk/superteamtr_back-print_on-dark_PRINTBUILD.eps` |
| DTG / DTF shop | `production/png-300dpi/*_PRINTBUILD_300dpi_transparent.png` (or `_FULLCOLOR_dtg` for the gradient) |
| Design agency / brand | `design/final/*.svg` + `design/final/*.placements.json` |
| Marketplace print-on-demand | `production/png-300dpi/final-back-print_on-dark_FULLCOLOR_dtg_300dpi_transparent.png` |
| Embroiderer | `production/pdf-spot/superteamtr_front-chest_on-dark_SPOT-PANTONE.pdf` (vector spot art, scaled to 40–60 mm) |
| Photoshop / retouch / mockup studio | `production/psd/*.psd` (5 layered files, spot-named ink layers) |
| Web / social | `mockups/*.png`, `design/final/*.svg` |

---

## 7. File formats in the package (summary)

| Format | Where | Notes |
|---|---|---|
| SVG (master, RGB + gradient) | `design/final/`, `design/concepts/`, `production/svg/` | editable, out­lined type, provenance header |
| PDF (vector, CMYK) | `production/pdf-cmyk/` | print builds on garment-coloured pages |
| EPS (vector, CMYK) | `production/eps-cmyk/` | no background — ink artwork only |
| PDF films | `production/separations/` | 4-ink, 2-ink, 1-ink + underbase union plate |
| PNG 300 dpi | `production/png-300dpi/` | transparent, exact print size |
| TIFF CMYK | `production/tiff-300dpi/` | soft proofs (LZW) |
| PDF (spot / Pantone) | `production/pdf-spot/` | true `/Separation` plates, one film per ink |
| EPS (spot / Pantone) | `production/eps-spot/` | Separation colour space + DSC custom-ink names |
| PSD layered | `production/psd/` | 5 files: back dark, back light, front chest, full-colour back, and an all-panels 1:1 sheet — layers named after the Pantone inks (`01_SPOT_PANTONE_White_C` … `04_SPOT_PANTONE_338_C`) + print guide + hidden master |

Full list with sizes and hashes: `docs/09-deliverables-manifest.md`.
