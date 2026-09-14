"""
build_presentation.py -- generates a single self-contained index.html board.

Every image is embedded as a downscaled JPEG data URI, so the page renders with
no network access (works inside sandboxed previews and offline hand-offs).

Run:  python3 tools/build_presentation.py
"""
from __future__ import annotations

import base64
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_uri(rel: str, width: int = 900, quality: int = 80) -> str:
    path = os.path.join(ROOT, rel)
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


CARDS = [
    ("The hero build", "mockups/mockup-back-view.png",
     "Back print, washed black. 320 × 400 mm, 95 mm below the neck rib. "
     "Arena emblem → SuperteamTR lockup → tagline → Solana logotype."),
    ("Front chest mark", "mockups/mockup-front-view.png",
     "90 × 104 mm on the wearer's right chest, 95 mm below the shoulder seam."),
    ("Flat lay — light garment", "mockups/mockup-flatlay-back.png",
     "The same print reversed for a bone garment: black + brand inks."),
    ("Print detail (2×)", "mockups/mockup-detail-closeup.png",
     "110 × 62 mm of the real file — arcade walls 0.9 mm, finest tick 0.42 mm."),
    ("Placement sheet", "mockups/mockup-print-placement.png",
     "Every measurement a print shop needs, front and back."),
    ("Artwork only", "mockups/artwork-only-neutral.png",
     "The production artwork on neutral grey, at its true 4:5 ratio."),
]

CONCEPTS = [
    ("Concept 1 · ARENA PROTOCOL", "mockups/concept-1-mockup-back.png",
     "The recommended direction: Colosseum plan view rebuilt as a live network."),
    ("Concept 2 · SHEET 02/03", "mockups/concept-2-mockup-back.png",
     "Architectural elevation + validator mesh. 1–2 inks, cheapest to print."),
    ("Concept 3 · THE SEAL", "mockups/concept-3-mockup-front.png",
     "Premium roundel for chest, sleeve, embroidery and merch extensions."),
]


def main() -> None:
    cards = "\n".join(
        f'''    <figure class="card">
      <img src="{data_uri(src)}" alt="{title}">
      <figcaption><h3>{title}</h3><p>{note}</p></figcaption>
    </figure>''' for title, src, note in CARDS)

    concepts = "\n".join(
        f'''    <figure class="card small">
      <img src="{data_uri(src, 720, 78)}" alt="{title}">
      <figcaption><h3>{title}</h3><p>{note}</p></figcaption>
    </figure>''' for title, src, note in CONCEPTS)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SuperteamTR T-Shirt — ARENA PROTOCOL</title>
<style>
  :root {{
    --ink:#0d0d10; --paper:#f4f2ee; --red:#D6223B; --purple:#9945FF;
    --green:#14F195; --muted:#6b6b72;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:"Helvetica Neue",Arial,sans-serif; line-height:1.5;
  }}
  header {{
    background:var(--ink); color:#fff; padding:64px 28px 56px;
    text-align:center; position:relative; overflow:hidden;
  }}
  header .ring {{
    width:210px; height:210px; margin:0 auto 26px; border-radius:50%;
    border:2px solid rgba(255,255,255,.55);
    box-shadow:0 0 0 12px rgba(255,255,255,.07), 0 0 0 30px rgba(255,255,255,.04);
    display:flex; align-items:center; justify-content:center;
    background:radial-gradient(circle at 50% 45%, rgba(153,69,255,.35), transparent 62%);
  }}
  header .ring span {{
    font-size:34px; letter-spacing:.06em; font-weight:800;
  }}
  h1 {{ font-size:clamp(28px,5vw,52px); margin:0 0 10px; letter-spacing:.01em; }}
  header p {{ max-width:720px; margin:0 auto; color:#c9c9d1; }}
  .tags {{ margin-top:22px; display:flex; gap:10px; flex-wrap:wrap; justify-content:center; }}
  .tags span {{
    border:1px solid rgba(255,255,255,.3); border-radius:999px;
    padding:6px 14px; font-size:12.5px; letter-spacing:.08em; text-transform:uppercase;
  }}
  main {{ max-width:1180px; margin:0 auto; padding:56px 24px 80px; }}
  h2 {{
    font-size:13px; letter-spacing:.22em; text-transform:uppercase; color:var(--muted);
    margin:56px 0 22px; border-bottom:1px solid #ddd8d0; padding-bottom:10px;
  }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:26px; }}
  .grid.three {{ grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); }}
  .card {{
    margin:0; background:#fff; border-radius:14px; overflow:hidden;
    box-shadow:0 10px 30px rgba(20,20,25,.09), 0 1px 0 rgba(0,0,0,.04);
    display:flex; flex-direction:column;
  }}
  .card img {{ width:100%; display:block; background:#e9e7e3; }}
  .card figcaption {{ padding:16px 18px 20px; }}
  .card h3 {{ margin:0 0 6px; font-size:16px; letter-spacing:.01em; }}
  .card p {{ margin:0; font-size:13.5px; color:var(--muted); }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; background:#fff;
           border-radius:12px; overflow:hidden; box-shadow:0 6px 20px rgba(20,20,25,.06); }}
  th,td {{ text-align:left; padding:11px 14px; border-bottom:1px solid #eee9e2; }}
  th {{ background:#15151a; color:#fff; font-weight:600; font-size:12.5px;
        letter-spacing:.08em; text-transform:uppercase; }}
  tr:last-child td {{ border-bottom:none; }}
  code {{ background:#eee9e2; padding:2px 6px; border-radius:5px; font-size:13px; }}
  .swatches {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; }}
  .sw {{ border-radius:12px; overflow:hidden; box-shadow:0 6px 18px rgba(20,20,25,.08); background:#fff; }}
  .sw .chip {{ height:78px; }}
  .sw .meta {{ padding:10px 12px 12px; font-size:12.5px; }}
  .sw .meta b {{ display:block; font-size:13px; }}
  footer {{ background:var(--ink); color:#9d9da8; padding:34px 24px; text-align:center; font-size:13px; }}
  a {{ color:var(--purple); }}
</style>
</head>
<body>
<header>
  <div class="ring"><span>ST</span></div>
  <h1>ARENA PROTOCOL</h1>
  <p>SuperteamTR T-shirt — a Colosseum rebuilt as a futuristic Web3 arena, with the
     official Solana logomark at its centre. Production-ready vector artwork,
     separations, mockups and documentation.</p>
  <div class="tags">
    <span>320 × 400 mm back print</span><span>4 inks · 2 inks · 1 ink</span>
    <span>SVG · PDF · EPS · PSD · PNG · TIFF</span><span>Official brand assets only</span>
  </div>
</header>
<main>
  <h2>The deliverable</h2>
  <div class="grid">
{cards}
  </div>

  <h2>Three directions explored</h2>
  <div class="grid three">
{concepts}
  </div>

  <h2>Print specification</h2>
  <table>
    <tr><th>Item</th><th>Specification</th></tr>
    <tr><td>Back print</td><td>320 × 400 mm · centred · 95 mm below the neck rib</td></tr>
    <tr><td>Front chest</td><td>90 × 104 mm · 95 mm below the shoulder seam · 95 mm from centre (wearer's right)</td></tr>
    <tr><td>Neck label / sleeve</td><td>64 × 26 mm inside the neck · optional 40 mm sleeve circle</td></tr>
    <tr><td>Garment</td><td>washed black <code>#17171A</code>, 220–260 gsm combed cotton (alt: bone <code>#E9E4D8</code>)</td></tr>
    <tr><td>Type</td><td>Anton · Space Grotesk · JetBrains Mono — all converted to outlines (OFL fonts)</td></tr>
    <tr><td>Line weights</td><td>0.35 mm minimum hairline · 0.9 mm arcade walls · smallest type 8 pt</td></tr>
    <tr><td>Builds</td><td>full colour (DTG/DTF) · 4-ink screen print · 2-colour · 1-colour</td></tr>
  </table>

  <h2>Ink system</h2>
  <div class="swatches">
    <div class="sw"><div class="chip" style="background:#FFFFFF;border-bottom:1px solid #eee"></div>
      <div class="meta"><b>White base</b>#FFFFFF · CMYK 0/0/0/0</div></div>
    <div class="sw"><div class="chip" style="background:#D6223B"></div>
      <div class="meta"><b>SuperteamTR red</b>#D6223B · CMYK 6/95/72/0 · Pantone 199 C</div></div>
    <div class="sw"><div class="chip" style="background:#9945FF"></div>
      <div class="meta"><b>Solana purple</b>#9945FF · CMYK 68/79/0/0 · 2665 C</div></div>
    <div class="sw"><div class="chip" style="background:#28E0B9"></div>
      <div class="meta"><b>Solana teal</b>#28E0B9 · CMYK 52/0/38/0 · 338 C</div></div>
    <div class="sw"><div class="chip" style="background:#14F195"></div>
      <div class="meta"><b>Solana green</b>#14F195 · CMYK 55/0/60/0 · 802 C</div></div>
    <div class="sw"><div class="chip" style="background:#0B0B10"></div>
      <div class="meta"><b>Blueprint black</b>#0B0B10 · CMYK 60/55/55/100</div></div>
  </div>

  <h2>Quality control</h2>
  <table>
    <tr><th>Check</th><th>Result</th></tr>
    <tr><td>Official SuperteamTR + Solana logos, verified by sha256</td><td>✅ pass</td></tr>
    <tr><td>All type outlined · English only · no fake logos</td><td>✅ pass</td></tr>
    <tr><td>One / two / four-colour builds + separations</td><td>✅ pass</td></tr>
    <tr><td>CMYK vector PDF + EPS · 300 dpi transparent PNG · layered PSD</td><td>✅ pass</td></tr>
    <tr><td>Mockups composited at true 1:1 print scale</td><td>✅ pass</td></tr>
    <tr><td>Brand approval · Pantone draw-down · physical proof · gradient decision</td><td>⏳ human sign-off</td></tr>
  </table>
  <p style="font-size:13.5px;color:var(--muted)">
    Full report: <code>docs/08-quality-control.md</code> · file manifest with hashes:
    <code>docs/09-deliverables-manifest.md</code>.
  </p>
</main>
<footer>
  SuperteamTR · Solana ecosystem, Istanbul — official brand assets used unmodified.
  Artwork, toolkit and documentation generated as original vector work.
</footer>
</body>
</html>
'''
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("  ✓ index.html", f"{os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
