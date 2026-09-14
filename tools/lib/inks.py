"""
inks.py -- single source of truth for the print ink system.

Every ink carries: hex (screen), CMYK build (print), nearest Pantone reference
and the role it plays in the artwork.
"""
from __future__ import annotations

INK = {
    # key ink: garment colour / light ink
    "WHITE": dict(
        hex="#FFFFFF",
        cmyk=(0.0, 0.0, 0.0, 0.0),
        pantone="White (opaque plastisol / DTG white underbase)",
        spot="PANTONE White C",
        role="Primary light ink on dark garments; also the underbase for every "
             "colour separation when printing on black.",
    ),
    # SuperteamTR brand red (the controlled 'Turkish red' accent)
    "TR_RED": dict(
        hex="#D6223B",
        cmyk=(0.06, 0.95, 0.72, 0.00),
        pantone="199 C (nearest)",
        spot="PANTONE 199 C",
        role="Turkish / SuperteamTR accent - gates, bridge terminus nodes, "
             "index marks. Used sparingly (<= 8% of ink area).",
    ),
    # Solana brand purple
    "SOLANA_PURPLE": dict(
        hex="#9945FF",
        cmyk=(0.68, 0.79, 0.00, 0.00),
        pantone="2665 C (nearest)",
        spot="PANTONE 2665 C",
        role="Solana logomark gradient start + player-portal halo.",
    ),
    # Solana brand green
    "SOLANA_GREEN": dict(
        hex="#14F195",
        cmyk=(0.55, 0.00, 0.60, 0.00),
        pantone="3385 C / 802 C neon (nearest)",
        spot="PANTONE 802 C",
        role="Solana logomark gradient end + frame index marks.",
    ),
    # mid tone of the Solana gradient (used for the 2-colour print fallback)
    "SOLANA_TEAL": dict(
        hex="#28E0B9",
        cmyk=(0.52, 0.00, 0.38, 0.00),
        pantone="338 C (nearest)",
        spot="PANTONE 338 C",
        role="Mid step of the purple -> green gradient; second colour of the "
             "2-ink print fallback.",
    ),
    # blueprint concept
    "BLUEPRINT_BLACK": dict(
        hex="#0B0B10",
        cmyk=(0.60, 0.55, 0.55, 1.00),
        pantone="Black 6 C (nearest)",
        spot="PANTONE Black 6 C",
        role="Concept 2 line work on bone garments.",
    ),
    # garment colours
    "GARMENT_WASHED_BLACK": dict(
        hex="#17171A", cmyk=(0.65, 0.60, 0.55, 0.95),
        pantone="-", role="Recommended garment: washed / vintage black tee.",
    ),
    "GARMENT_OFF_WHITE": dict(
        hex="#E9E4D8", cmyk=(0.06, 0.06, 0.14, 0.00),
        pantone="Bone / 9224 C (nearest)",
        role="Alternate garment: bone / natural cotton tee.",
    ),
    "GARMENT_CHARCOAL": dict(
        hex="#2B2B2F", cmyk=(0.60, 0.52, 0.48, 0.72),
        pantone="447 C (nearest)", role="Alternate garment: charcoal.",
    ),
}

# Screen-print separation order for the hero artwork (back print)
HERO_SEPARATIONS = ["WHITE", "TR_RED", "SOLANA_PURPLE", "SOLANA_GREEN"]

# Full-colour -> limited print palette mapping used when the pure gradient is
# replaced by flat / two-ink buildable art.
GRADIENT_PRINT_MAP = {
    "#9945ff": INK["SOLANA_PURPLE"]["hex"],
    "#8752f3": INK["SOLANA_PURPLE"]["hex"],
    "#5497d5": INK["SOLANA_TEAL"]["hex"],
    "#43b4ca": INK["SOLANA_TEAL"]["hex"],
    "#28e0b9": INK["SOLANA_TEAL"]["hex"],
    "#19fb9b": INK["SOLANA_GREEN"]["hex"],
}


NAMED_COLOURS = {
    "white": "#FFFFFF", "black": "#000000", "none": "#000000",
    "red": "#FF0000", "green": "#00FF00", "blue": "#0000FF",
    "gray": "#808080", "grey": "#808080", "silver": "#C0C0C0",
}


def normalize_colour(color: str) -> str:
    """Resolve CSS colour names to hex so inks can be looked up reliably."""
    c = (color or "").strip()
    if not c:
        return "#000000"
    if c.startswith("#"):
        return c
    return NAMED_COLOURS.get(c.lower(), c)


def spot_name(hex_color: str) -> str:
    """Spot (Pantone) ink name for a colour; falls back to a named custom ink."""
    h = normalize_colour(hex_color).strip().lower()
    for ink in INK.values():
        if ink["hex"].lower() == h and ink.get("spot"):
            return ink["spot"]
    return f"Custom ink {h.upper()}"


def cmyk_of(hex_color: str) -> tuple[float, float, float, float]:
    hex_color = normalize_colour(hex_color)
    """Look up a CMYK build; fall back to a simple conversion for stray colours."""
    h = hex_color.strip().lower()
    for ink in INK.values():
        if ink["hex"].lower() == h:
            return ink["cmyk"]
    return rgb_to_cmyk(hex_to_rgb(h))


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_cmyk(rgb: tuple[int, int, int]) -> tuple[float, float, float, float]:
    r, g, b = [v / 255.0 for v in rgb]
    k = 1.0 - max(r, g, b)
    if k >= 1.0:
        return (0.0, 0.0, 0.0, 1.0)
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return (round(c, 3), round(m, 3), round(y, 3), round(k, 3))
