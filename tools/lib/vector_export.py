"""
vector_export.py -- production export engines for the artwork SVGs.

The artwork is drawn with FILLED paths only (no strokes, no filters), which makes
a compact, dependency-free vector pipeline possible:

    SVG (master, RGB, gradients)
        -> PDF / EPS   (CMYK, vector, gradient rendered as N-band blend approximation)
        -> CMYK TIFF   (soft-proof raster, 300 dpi)
        -> separation film files (one file per screen-print ink)

Path data support: M L H V C S Q T A Z, absolute and relative.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .inks import cmyk_of, hex_to_rgb, normalize_colour, spot_name

# --------------------------------------------------------------------------- #
#  path parsing (shared implementation)
# --------------------------------------------------------------------------- #

from .pathparse import Seg, bounds, parse_path  # noqa: E402


# --------------------------------------------------------------------------- #
#  SVG reading
# --------------------------------------------------------------------------- #

_PATH_RE = re.compile(r"<path\b([^>]*)/?>", re.I)
_ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')
_RECT_RE = re.compile(r"<rect\b([^>]*)/?>", re.I)
_GRAD_RE = re.compile(r'<linearGradient\b([^>]*)>(.*?)</linearGradient>', re.I | re.S)
_STOP_RE = re.compile(r'<stop\b([^>]*)/?>', re.I)


@dataclass
class SvgItem:
    subpaths: list[list[Seg]]
    fill: str
    opacity: float = 1.0
    gradient: dict | None = None


@dataclass
class SvgDoc:
    width: float
    height: float
    items: list[SvgItem]
    background: str | None = None


def _attrs(s: str) -> dict:
    return {k: v for k, v in _ATTR_RE.findall(s)}


def read_svg(svg_text: str) -> SvgDoc:
    root = re.search(r"<svg\b([^>]*)>", svg_text, re.I)
    ra = _attrs(root.group(1))
    w = float(re.sub(r"[^0-9.]", "", ra.get("width", "100")) or 100)
    h = float(re.sub(r"[^0-9.]", "", ra.get("height", "100")) or 100)

    grads: dict[str, dict] = {}
    for gm in _GRAD_RE.finditer(svg_text):
        ga = _attrs(gm.group(1))
        stops = []
        for sm in _STOP_RE.finditer(gm.group(2)):
            sa = _attrs(sm.group(1))
            stops.append((float(sa.get("offset", 0)), normalize_colour(sa.get("stop-color", "#000000"))))
        if stops:
            grads[ga.get("id", "")] = dict(
                stops=stops,
                x1=float(ga.get("x1", 0) or 0), y1=float(ga.get("y1", 0) or 0),
                x2=float(ga.get("x2", 1) or 1), y2=float(ga.get("y2", 0) or 0),
                units=ga.get("gradientUnits", "userSpaceOnUse"),
            )

    items: list[SvgItem] = []
    bg = None
    for rm in _RECT_RE.finditer(svg_text):
        a = _attrs(rm.group(1))
        if a.get("fill") and a.get("width") and a.get("height"):
            x, y = float(a.get("x", 0)), float(a.get("y", 0))
            rw, rh = float(a["width"]), float(a["height"])
            if rw >= w - 0.01 and rh >= h - 0.01:
                bg = a["fill"]
                continue
            items.append(SvgItem(subpaths=parse_path(
                f"M{x} {y}L{x + rw} {y}L{x + rw} {y + rh}L{x} {y + rh}Z"),
                fill=normalize_colour(a["fill"])))
    for pm in _PATH_RE.finditer(svg_text):
        a = _attrs(pm.group(1))
        d = a.get("d")
        if not d:
            continue
        fill = normalize_colour(a.get("fill", "#000000"))
        grad = None
        if fill.startswith("url(#"):
            gid = fill[5:-1]
            grad = grads.get(gid)
            fill = grad["stops"][0][1] if grad else "#000000"
        items.append(SvgItem(
            subpaths=parse_path(d), fill=fill,
            opacity=float(a.get("fill-opacity", 1) or 1), gradient=grad))
    return SvgDoc(width=w, height=h, items=items, background=bg)


# --------------------------------------------------------------------------- #
#  gradient -> band approximation
# --------------------------------------------------------------------------- #


def _lerp_hex(c0: str, c1: str, t: float) -> str:
    r0, g0, b0 = hex_to_rgb(c0)
    r1, g1, b1 = hex_to_rgb(c1)
    return "#%02X%02X%02X" % (
        round(r0 + (r1 - r0) * t),
        round(g0 + (g1 - g0) * t),
        round(b0 + (b1 - b0) * t),
    )


def gradient_color(grad: dict, t: float) -> str:
    stops = sorted(grad["stops"], key=lambda s: s[0])
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        o0, c0 = stops[i]
        o1, c1 = stops[i + 1]
        if o0 <= t <= o1:
            f = (t - o0) / (o1 - o0) if o1 > o0 else 0.0
            return _lerp_hex(c0, c1, f)
    return stops[-1][1]


def band_quads(grad: dict, bounds: tuple[float, float, float, float], bands: int):
    """Split the gradient into bands: returns [(confidence_t, quad_path_segments)]."""
    x1, y1, x2, y2 = grad["x1"], grad["y1"], grad["x2"], grad["y2"]
    ux, uy = x2 - x1, y2 - y1
    L = math.hypot(ux, uy) or 1.0
    ux, uy = ux / L, uy / L
    px, py = -uy, ux
    bx0, by0, bx1, by1 = bounds
    reach = math.hypot(bx1 - bx0, by1 - by0) * 1.5 + L
    cx0 = (bx0 + bx1) / 2.0 - ux * reach / 2.0
    cy0 = (by0 + by1) / 2.0 - uy * reach / 2.0
    origin = (cx0, cy0)
    out = []
    for k in range(bands):
        t0 = k / bands
        t1 = (k + 1) / bands
        a0 = (origin[0] + ux * reach * t0, origin[1] + uy * reach * t0)
        a1 = (origin[0] + ux * reach * t1, origin[1] + uy * reach * t1)
        quad = [
            Seg("M", (a0[0] + px * reach, a0[1] + py * reach)),
            Seg("L", (a1[0] + px * reach, a1[1] + py * reach)),
            Seg("L", (a1[0] - px * reach, a1[1] - py * reach)),
            Seg("L", (a0[0] - px * reach, a0[1] - py * reach)),
            Seg("Z", ()),
        ]
        out.append(((t0 + t1) / 2.0, [quad]))
    return out


def bounds_of(subpaths) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for sp in subpaths:
        for s in sp:
            if s.op != "Z":
                for i in range(0, len(s.pts), 2):
                    xs.append(s.pts[i])
                    ys.append(s.pts[i + 1])
    return (min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------------- #
#  PDF writer (CMYK, vector)
# --------------------------------------------------------------------------- #

MM2PT = 72.0 / 25.4


def _pdf_path_ops(subpaths) -> str:
    out = []
    for sp in subpaths:
        for s in sp:
            if s.op == "M":
                out.append(f"{s.pts[0]:.4f} {s.pts[1]:.4f} m")
            elif s.op == "L":
                out.append(f"{s.pts[0]:.4f} {s.pts[1]:.4f} l")
            elif s.op == "C":
                out.append(
                    f"{s.pts[0]:.4f} {s.pts[1]:.4f} {s.pts[2]:.4f} "
                    f"{s.pts[3]:.4f} {s.pts[4]:.4f} {s.pts[5]:.4f} c"
                )
            elif s.op == "Z":
                out.append("h")
    return "\n".join(out)


def _clip_ops(subpaths) -> str:
    return _pdf_path_ops(subpaths) + "\nW n"


def _pdf_name(name: str) -> str:
    """Escape a string into a legal PDF name object (spaces -> #20)."""
    out = []
    for ch in name:
        out.append(ch if (ch.isalnum() or ch in "-_.") else "#%02X" % ord(ch))
    return "".join(out)


class _SpotRegistry:
    """Collects the spot (Pantone) inks used in a page and the alternating
    DeviceCMYK alternate that the tint transform maps to."""

    def __init__(self, enabled: bool):
        self.enabled = enabled
        self.inks: dict[str, tuple[str, str, tuple]] = {}   # hex -> (res, name, cmyk)

    def of(self, colour: str) -> str:
        h = normalize_colour(colour).strip().lower()
        if h not in self.inks:
            self.inks[h] = (f"CS{len(self.inks)}", spot_name(h), cmyk_of(h))
        return self.inks[h][0]

    def resname(self, colour: str) -> str | None:
        h = normalize_colour(colour).strip().lower()
        e = self.inks.get(h)
        return e[0] if e else None


def svg_to_pdf(svg_text: str, out_path: str, *, bands: int = 10,
               gradient_flat_map: dict | None = None, separate_fill: str | None = None,
               force_fill: str | None = None, page_bg: str | None = None,
               film: bool = False, spot: bool = False, title: str = "") -> None:
    """Convert an artwork SVG to a vector PDF.

    spot=True  -> every ink is written as a real PDF /Separation colour space
                  named after its Pantone reference (with a DeviceCMYK tint
                  transform), so the file carries true spot plates instead of
                  process builds.
    separate_fill / film -> single-plate film positives (black on white).
    """
    doc = read_svg(svg_text)
    H = doc.height
    content: list[str] = []
    reg = _SpotRegistry(spot)
    content.append(f"q {MM2PT:.5f} 0 0 {-MM2PT:.5f} 0 {H * MM2PT:.4f} cm")

    def paint(color_hex: str) -> None:
        if spot:
            content.append(f"/{reg.of(color_hex)} cs 1 scn")
        else:
            c, m, y, k = cmyk_of(color_hex)
            content.append(f"{c:.3f} {m:.3f} {y:.3f} {k:.3f} k")

    if page_bg:
        paint(page_bg)
        content.append(f"0 0 {doc.width:.4f} {H:.4f} re f")

    def emit(color_hex: str, subpaths, opacity=1.0):
        if separate_fill and color_hex.lower() != separate_fill.lower():
            return                          # this item does not belong on this plate
        if film:
            color_hex = force_fill or "#000000"   # film positive: solid black
        elif force_fill:
            color_hex = force_fill
        paint(color_hex)
        content.append(_pdf_path_ops(subpaths))
        content.append("f*")

    for it in doc.items:
        if it.gradient and bands >= 1:
            grad = it.gradient
            if gradient_flat_map:
                grad = dict(grad)
                grad["stops"] = [(o, gradient_flat_map.get(c.lower(), c))
                                 for o, c in grad["stops"]]
            plate_colours = [c.lower() for _o, c in grad["stops"]]
            if separate_fill and separate_fill.lower() not in plate_colours:
                continue          # gradient mark belongs to another plate
            b = bounds_of(it.subpaths)
            if spot:
                distinct: list[str] = []
                for _o, cc in grad["stops"]:
                    if not distinct or distinct[-1].lower() != cc.lower():
                        distinct.append(cc)
                nb = max(1, len(distinct))
                if film or separate_fill:
                    distinct = [force_fill or "#000000"]
                    nb = 1
                for i, (_t, quad) in enumerate(band_quads(grad, b, nb)):
                    col = distinct[min(i, nb - 1)]
                    content.append("q")
                    content.append(_clip_ops(it.subpaths))
                    paint(col)
                    content.append(_pdf_path_ops(quad))
                    content.append("f")
                    content.append("Q")
                continue
            for t, quad in band_quads(grad, b, bands):
                col = "#000000" if (film or separate_fill) else gradient_color(grad, t)
                content.append("q")
                content.append(_clip_ops(it.subpaths))
                paint(col)
                content.append(_pdf_path_ops(quad))
                content.append("f")
                content.append("Q")
        else:
            emit(it.fill, it.subpaths, it.opacity)

    content.append("Q")
    stream = "\n".join(content).encode("latin-1")

    W_pt, H_pt = doc.width * MM2PT, doc.height * MM2PT
    objs: list[bytes] = []

    def obj(body: bytes) -> int:
        objs.append(body)
        return len(objs)

    info = obj(f"<< /Title ({title or 'SuperteamTR artwork'}) "
               f"/Producer (SuperteamTR design toolkit) "
               f"/Creator (tools/lib/vector_export.py) "
               f"/Subject ({'spot-colour separations' if spot else 'process CMYK artwork'}) "
               f">>".encode("latin-1"))

    fn_ref: dict[str, int] = {}
    for hexc, (res, _name, cmyk) in reg.inks.items():
        c, m, y, k = cmyk
        fn_ref[res] = obj(
            (f"<< /FunctionType 2 /Domain [0 1] /Range [0 1 0 1 0 1 0 1] "
             f"/C0 [0 0 0 0] /C1 [{c:.3f} {m:.3f} {y:.3f} {k:.3f}] /N 1 >>")
            .encode("latin-1"))

    contents = obj(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
                   + stream + b"\nendstream")

    if reg.inks:
        cs = " ".join(
            f"/{res} [/Separation /{_pdf_name(name)} /DeviceCMYK {fn_ref[res]} 0 R]"
            for res, name, _cmyk in reg.inks.values())
        resources = f"<< /ColorSpace << {cs} >> >>"
    else:
        resources = "<< >>"

    page = obj((f"<< /Type /Page /Parent 4 0 R /MediaBox [0 0 {W_pt:.4f} {H_pt:.4f}] "
                f"/Contents {contents} 0 R /Resources {resources} >>").encode("latin-1"))
    pages = obj(b"<< /Type /Pages /Kids [" + f"{page} 0 R".encode() + b"] /Count 1 >>")
    catalog = obj(f"<< /Type /Catalog /Pages {pages} 0 R >>".encode("latin-1"))

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs) + 1} /Root {catalog} 0 R /Info {info} 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n").encode()
    with open(out_path, "wb") as fh:
        fh.write(bytes(out))


# --------------------------------------------------------------------------- #
#  EPS writer (CMYK or spot, vector)
# --------------------------------------------------------------------------- #


def _ps_path_ops(subpaths) -> str:
    out = []
    for sp in subpaths:
        for s in sp:
            if s.op == "M":
                out.append(f"{s.pts[0] * MM2PT:.4f} {s.pts[1] * MM2PT:.4f} moveto")
            elif s.op == "L":
                out.append(f"{s.pts[0] * MM2PT:.4f} {s.pts[1] * MM2PT:.4f} lineto")
            elif s.op == "C":
                p = [v * MM2PT for v in s.pts]
                out.append(f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} {p[3]:.4f} "
                           f"{p[4]:.4f} {p[5]:.4f} curveto")
            elif s.op == "Z":
                out.append("closepath")
    return "\n".join(out)


def _ps_separation(name: str, cmyk: tuple) -> str:
    """PostScript Level 3 Separation colour space with a linear CMYK tint
    transform (tint on the stack -> C M Y K), so the ink stays a spot plate."""
    c, m, y, k = cmyk
    return (f"[/Separation ({name}) /DeviceCMYK "
            f"{{ dup {c:.4f} mul exch dup {m:.4f} mul exch dup {y:.4f} mul exch "
            f"{k:.4f} mul }}] setcolorspace")


def svg_to_eps(svg_text: str, out_path: str, *, bands: int = 10,
               gradient_flat_map: dict | None = None, separate_fill: str | None = None,
               force_fill: str | None = None, page_bg: str | None = None,
               film: bool = False, spot: bool = False, title: str = "") -> None:
    doc = read_svg(svg_text)
    W, H = doc.width * MM2PT, doc.height * MM2PT
    reg = _SpotRegistry(spot)

    def paint(color_hex: str) -> None:
        if spot:
            code, name, cmyk = (reg.resname(color_hex) or reg.of(color_hex),
                                spot_name(color_hex), cmyk_of(color_hex))
            lines.append(f"% spot ink: {name}")
            lines.append(_ps_separation(name, cmyk))
            lines.append("1 setcolor")
        else:
            c, m, y, k = cmyk_of(color_hex)
            lines.append(f"{c:.3f} {m:.3f} {y:.3f} {k:.3f} setcmykcolor")

    if page_bg:
        bg_c, bg_m, bg_y, bg_k = cmyk_of(page_bg)
        bg_line = (f"{bg_c:.3f} {bg_m:.3f} {bg_y:.3f} {bg_k:.3f} setcmykcolor "
                   f"0 0 {W:.4f} {H:.4f} rectfill")
    else:
        bg_line = "% no page background (ink artwork only)"

    lines = [
        "%!PS-Adobe-3.0 EPSF-3.0",
        f"%%BoundingBox: 0 0 {math.ceil(W)} {math.ceil(H)}",
        f"%%HiResBoundingBox: 0 0 {W:.4f} {H:.4f}",
        f"%%Title: {title or 'SuperteamTR artwork'}",
        "%%Creator: SuperteamTR design toolkit (tools/lib/vector_export.py)",
        "%%LanguageLevel: 3",
    ]
    if spot:
        # DSC spot-colour declarations (used by Illustrator / InDesign on import)
        names = []
        for hexc in dict.fromkeys(_colours_in(doc)):
            names.append(spot_name(hexc))
        lines.append("%%DocumentProcessColors: Cyan Magenta Yellow Black")
        lines.append("%%DocumentCustomColors: " + " ".join(f"({n})" for n in names))
        for hexc in dict.fromkeys(_colours_in(doc)):
            c, m, y, k = cmyk_of(hexc)
            lines.append(f"%%CMYKCustomColor: {c:.3f} {m:.3f} {y:.3f} {k:.3f} "
                         f"({spot_name(hexc)})")
    else:
        lines.append("%%DocumentProcessColors: Cyan Magenta Yellow Black")
    lines += [
        "%%EndComments",
        "%%BeginProlog",
        "/m {moveto} bind def /l {lineto} bind def /c {curveto} bind def",
        "%%EndProlog",
        "%%BeginSetup",
        "gsave",
        f"0 {H:.4f} translate 1 -1 scale",
        bg_line,
        "%%EndSetup",
    ]

    def emit(color_hex, subpaths):
        if separate_fill and color_hex.lower() != separate_fill.lower():
            return
        if film:
            color_hex = force_fill or "#000000"
        elif force_fill:
            color_hex = force_fill
        paint(color_hex)
        lines.append(_ps_path_ops(subpaths))
        lines.append("eofill")

    for it in doc.items:
        if it.gradient and bands >= 1:
            grad = it.gradient
            if gradient_flat_map:
                grad = dict(grad)
                grad["stops"] = [(o, gradient_flat_map.get(cc.lower(), cc))
                                 for o, cc in grad["stops"]]
            plate_colours = [cc.lower() for _o, cc in grad["stops"]]
            if separate_fill and separate_fill.lower() not in plate_colours:
                continue
            b = bounds_of(it.subpaths)
            if spot:
                distinct: list[str] = []
                for _o, cc in grad["stops"]:
                    if not distinct or distinct[-1].lower() != cc.lower():
                        distinct.append(cc)
                nb = max(1, len(distinct))
                if film or separate_fill:
                    distinct, nb = [force_fill or "#000000"], 1
                for i, (_t, quad) in enumerate(band_quads(grad, b, nb)):
                    col = distinct[min(i, nb - 1)]
                    lines.append("gsave")
                    lines.append(_ps_path_ops(it.subpaths))
                    lines.append("eoclip")
                    paint(col)
                    lines.append(_ps_path_ops(quad))
                    lines.append("eofill")
                    lines.append("grestore")
                continue
            for t, quad in band_quads(grad, b, bands):
                col = "#000000" if (film or separate_fill) else gradient_color(grad, t)
                lines.append("gsave")
                lines.append(_ps_path_ops(it.subpaths))
                lines.append("eoclip")
                c, m, y, k = cmyk_of(col)
                lines.append(f"{c:.3f} {m:.3f} {y:.3f} {k:.3f} setcmykcolor")
                lines.append(_ps_path_ops(quad))
                lines.append("eofill")
                lines.append("grestore")
        else:
            emit(it.fill, it.subpaths)

    lines += ["grestore", "showpage", "%%EOF"]
    with open(out_path, "w", encoding="latin-1") as fh:
        fh.write("\n".join(lines) + "\n")


def _colours_in(doc) -> list[str]:
    """Ink colours used by a document, in first-use order."""
    out: list[str] = []
    for it in doc.items:
        cols = [it.fill]
        if it.gradient:
            cols += [c for _o, c in it.gradient["stops"]]
        for c in cols:
            if c.lower() not in [x.lower() for x in out]:
                out.append(c)
    return out
