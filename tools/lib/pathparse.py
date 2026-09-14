"""
pathparse.py -- dependency-free SVG path parser.

Converts any SVG path data (M L H V C S Q T A Z, absolute or relative, with
implicit command repetition) into a flat list of absolute subpaths made of
'M' / 'L' / 'C' / 'Z' segments only.  That normalised form is what the PDF, EPS
and raster pipelines consume, so every downstream tool speaks one dialect.

Used by:  tools/lib/svgutil.py (brand asset import)
          tools/lib/vector_export.py (PDF / EPS writers)
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass


@dataclass
class Seg:
    op: str  # 'M' | 'L' | 'C' | 'Z'
    pts: tuple = ()

    def moved(self, m, dy: float = 0.0) -> "Seg":
        a0, a1, a2, a3, a4, a5 = m
        pts = []
        for i in range(0, len(self.pts), 2):
            px, py = self.pts[i], self.pts[i + 1]
            pts += [a0 * px + a2 * py + a4, a1 * px + a3 * py + a5]
        return Seg(self.op, tuple(pts))


_CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")


def _numbers(s: str) -> list[float]:
    return [float(v) for v in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", s)]


def _arc_to_cubics(x1, y1, rx, ry, phi_deg, large_arc, sweep, x2, y2):
    if rx == 0 or ry == 0 or (x1 == x2 and y1 == y2):
        return [("L", (x2, y2))]
    phi = math.radians(phi_deg % 360)
    cosp, sinp = math.cos(phi), math.sin(phi)
    dx2, dy2 = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p = cosp * dx2 + sinp * dy2
    y1p = -sinp * dx2 + cosp * dy2
    rx, ry = abs(rx), abs(ry)
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large_arc == sweep:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx
    cx = cosp * cxp - sinp * cyp + (x1 + x2) / 2.0
    cy = sinp * cxp + cosp * cyp + (y1 + y2) / 2.0

    def ang(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        nrm = math.hypot(ux, uy) * math.hypot(vx, vy)
        a = math.acos(max(-1.0, min(1.0, dot / (nrm or 1.0))))
        return -a if (ux * vy - uy * vx) < 0 else a

    theta1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep and dtheta < 0:
        dtheta += 2 * math.pi

    segs = max(1, int(math.ceil(abs(dtheta) / (math.pi / 2))))
    delta = dtheta / segs
    k = 4.0 / 3.0 * math.tan(delta / 4.0)
    out = []
    t = theta1
    for _ in range(segs):
        a0, a1 = t, t + delta
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        p1 = (cx + rx * cosp * (c0 - k * s0) - ry * sinp * (s0 + k * c0),
              cy + rx * sinp * (c0 - k * s0) + ry * cosp * (s0 + k * c0))
        p3 = (cx + rx * cosp * c1 - ry * sinp * s1, cy + rx * sinp * c1 + ry * cosp * s1)
        p2 = (cx + rx * cosp * (c1 + k * s1) - ry * sinp * (s1 - k * c1),
              cy + rx * sinp * (c1 + k * s1) + ry * cosp * (s1 - k * c1))
        out.append(("C", (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])))
        t = a1
    return out


def parse_path(d: str) -> list[list[Seg]]:
    """Normalise path data into absolute subpaths of M / L / C / Z segments."""
    subpaths: list[list[Seg]] = []
    cur: list[Seg] = []
    x = y = 0.0
    sx = sy = 0.0
    prev_ctrl = None
    prev_qctrl = None

    for cmd, arg_str in _CMD_RE.findall(d):
        nums = _numbers(arg_str)
        up = cmd.upper()
        rel = cmd.islower()
        i = 0

        if up == "Z":
            cur.append(Seg("Z", ()))
            x, y = sx, sy
            prev_ctrl = prev_qctrl = None
            continue

        if up == "M":
            first = True
            while i + 1 < len(nums):
                px, py = nums[i], nums[i + 1]
                i += 2
                if rel:
                    px, py = x + px, y + py
                if first:
                    if cur:
                        subpaths.append(cur)
                    cur = [Seg("M", (px, py))]
                    sx, sy = px, py
                    first = False
                else:
                    cur.append(Seg("L", (px, py)))
                x, y = px, py
            prev_ctrl = prev_qctrl = None
            continue

        while i < len(nums):
            if up == "L":
                if i + 1 >= len(nums):
                    break
                px, py = nums[i], nums[i + 1]
                i += 2
                if rel:
                    px, py = x + px, y + py
                cur.append(Seg("L", (px, py)))
                x, y = px, py
                prev_ctrl = prev_qctrl = None
            elif up == "H":
                px = nums[i]
                i += 1
                if rel:
                    px = x + px
                cur.append(Seg("L", (px, y)))
                x = px
                prev_ctrl = prev_qctrl = None
            elif up == "V":
                py = nums[i]
                i += 1
                if rel:
                    py = y + py
                cur.append(Seg("L", (x, py)))
                y = py
                prev_ctrl = prev_qctrl = None
            elif up == "C":
                if i + 5 >= len(nums):
                    break
                vals = nums[i:i + 6]
                i += 6
                if rel:
                    vals = [x + vals[0], y + vals[1], x + vals[2], y + vals[3],
                            x + vals[4], y + vals[5]]
                cur.append(Seg("C", tuple(vals)))
                prev_ctrl = (vals[2], vals[3])
                prev_qctrl = None
                x, y = vals[4], vals[5]
            elif up == "S":
                if i + 3 >= len(nums):
                    break
                vals = nums[i:i + 4]
                i += 4
                if rel:
                    vals = [x + vals[0], y + vals[1], x + vals[2], y + vals[3]]
                c1 = (2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1]) if prev_ctrl else (x, y)
                cur.append(Seg("C", (c1[0], c1[1], vals[0], vals[1], vals[2], vals[3])))
                prev_ctrl = (vals[0], vals[1])
                prev_qctrl = None
                x, y = vals[2], vals[3]
            elif up == "Q":
                if i + 3 >= len(nums):
                    break
                qx, qy, ex, ey = nums[i:i + 4]
                i += 4
                if rel:
                    qx, qy, ex, ey = x + qx, y + qy, x + ex, y + ey
                c1 = (x + 2.0 / 3.0 * (qx - x), y + 2.0 / 3.0 * (qy - y))
                c2 = (ex + 2.0 / 3.0 * (qx - ex), ey + 2.0 / 3.0 * (qy - ey))
                cur.append(Seg("C", (c1[0], c1[1], c2[0], c2[1], ex, ey)))
                prev_ctrl = None
                prev_qctrl = (qx, qy)
                x, y = ex, ey
            elif up == "T":
                if i + 1 >= len(nums):
                    break
                ex, ey = nums[i], nums[i + 1]
                i += 2
                if rel:
                    ex, ey = x + ex, y + ey
                qx, qy = (2 * x - prev_qctrl[0], 2 * y - prev_qctrl[1]) if prev_qctrl else (x, y)
                c1 = (x + 2.0 / 3.0 * (qx - x), y + 2.0 / 3.0 * (qy - y))
                c2 = (ex + 2.0 / 3.0 * (qx - ex), ey + 2.0 / 3.0 * (qy - ey))
                cur.append(Seg("C", (c1[0], c1[1], c2[0], c2[1], ex, ey)))
                prev_qctrl = (qx, qy)
                prev_ctrl = None
                x, y = ex, ey
            elif up == "A":
                if i + 6 >= len(nums):
                    break
                rx, ry, rot, laf, sf, ex, ey = nums[i:i + 7]
                i += 7
                if rel:
                    ex, ey = x + ex, y + ey
                for op, pts in _arc_to_cubics(x, y, rx, ry, rot, int(laf), int(sf), ex, ey):
                    cur.append(Seg(op, pts))
                x, y = ex, ey
                prev_ctrl = prev_qctrl = None
            else:  # pragma: no cover
                break
    if cur:
        subpaths.append(cur)
    return subpaths


def fmt(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def subpaths_to_d(subpaths: list[list[Seg]]) -> str:
    out = []
    for sp in subpaths:
        for s in sp:
            if s.op == "M":
                out.append(f"M{fmt(s.pts[0])} {fmt(s.pts[1])}")
            elif s.op == "L":
                out.append(f"L{fmt(s.pts[0])} {fmt(s.pts[1])}")
            elif s.op == "C":
                out.append("C" + " ".join(fmt(v) for v in s.pts))
            elif s.op == "Z":
                out.append("Z")
    return "".join(out)


def transform_d(d: str, m) -> str:
    """Apply an affine matrix (a,b,c,d,e,f) to path data, re-emitting M/L/C/Z."""
    return subpaths_to_d([[s.moved(m) for s in sp] for sp in parse_path(d)])


def bounds(subpaths) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for sp in subpaths:
        for s in sp:
            for i in range(0, len(s.pts), 2):
                xs.append(s.pts[i])
                ys.append(s.pts[i + 1])
    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))
