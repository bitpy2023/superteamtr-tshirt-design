# 01 · Creative strategy

**Project:** SuperteamTR T-Shirt — *Colosseum / Crypto World Expo inspired*
**Client:** SuperteamTR — the Turkish chapter of the global Superteam network
(Solana ecosystem builders, creators, developers and Web3 projects in Türkiye)
**Deliverable type:** production-ready event / community merchandise
**Language rule:** all visible artwork text is English

---

## 1. What we are actually making

Not a "crypto T-shirt". We are making the *physical badge of a builder arena*:
the shirt a Turkish Solana developer wears to a hackathon final, an expo booth,
a demo day — and still wears on a Tuesday. The Colosseum reference is used as
**structure** (an arena where builders compete and gather), never as costume:
no gladiators, no Roman columns, no togas, no laurel wreaths, no photographic
stone textures.

## 2. Strategic objectives

| # | Objective | How the artwork delivers it |
|---|---|---|
| 1 | Read as **SuperteamTR** at first glance | Official SuperteamTR lockup is the largest brand shape on the back print, immediately under the arena; the "superteam türkiye" wordmark is unmistakable from 5 m |
| 2 | Read as **Solana ecosystem** | The official Solana logomark sits at the exact centre of the arena (a "core protocol" at the centre of the ring); official Solana logotype anchors the bottom of the back print; purple→green gradient carries the ecosystem energy |
| 3 | Feel like a **futuristic arena / expo** | The main graphic is a plan-view Colosseum: two real arcade tiers, gates, arena floor, seating, telemetry ring and node ring — a stadium seen from the air with a blockchain network laid over it |
| 4 | Be **wearable**, not cosplay | Restrained four-ink palette on washed black, generous negative space, no photographic texture, structure built from clean vector geometry. The graphic reads as a premium emblem, not a poster on a shirt |
| 5 | Be **print-feasible everywhere** | Minimum line weight 0.35 mm, no opacity stacks, four flat inks + one buildable gradient, with 2-ink and 1-ink fallbacks and a screen-print separation set |
| 6 | Be **scalable** | One master emblem drives the 320 × 400 mm back print, the 90 × 104 mm front chest mark, the 40 mm sleeve mark, the neck label and a 40–60 mm embroidery adaptation — all from the same geometry |

## 3. Audience

* Solana/Türkiye **builders**: devs, designers, founders, students at the
  Istanbul / Ankara / Izmir meetups and hackathons.
* **Global** Superteam members and Solana Foundation guests who will see the
  shirt at international events — hence English-only lettering and no
  tourist-cliché Turkish symbols.
* Merch-savvy buyers who judge fabric, print quality and restraint — the shirt
  has to survive close inspection at a booth.

## 4. Constraints we held ourselves to

**Brand**
* Official logo files only — no redrawing, no distortion, no rotation, no
  creative re-interpretation. Sources, hashes and placements are documented in
  `docs/10-assets-and-licensing.md` and sidecar `*.placements.json` files.
* Clear space around both marks (≥ 0.5 × logo height), never inside another
  element's bounding box.

**Turkish identity — subtle, not cliché**
* The **brand red `#D6223B`** (the actual SuperteamTR red) is the only
  national colour, and it is used as a *technical accent*: gate keystones,
  bridge terminus nodes, index marks and gate rail — ≤ 8 % of ink area.
  No flags, no oversized crescents or stars beyond the official monogram.
* **Istanbul coordinates 41.0082° N / 28.9784° E** printed as technical data
  in the header row — a location stamp, not a souvenir motif.
* The **East–West axis** that runs through the arena is a dashed signal line
  bridging two landmarks: a restrained metaphor for Türkiye as the bridge
  between regions (and for cross-chain interoperability), readable as pure
  technical drawing.

**Production**
* Filled vector shapes only, no strokes thinner than 0.35 mm, no photographic
  texture, no uncontrolled transparency, no detail below 8 pt type.
* Must survive: full colour, two colours, one colour.

## 5. Quality bar (what "no" looks like)

Rejected on sight: generic Bitcoin/coin symbols, random neon cyberpunk,
circuit-board filler, fake logos, unreadable type, heavy 3D bevels, clip-art
Romans, conference-badge layouts pasted on a chest. If an element does not
carry meaning, it was cut. Every mark in the final artwork is one of:
arena architecture · network topology · measurement/telemetry · brand · type.

## 6. How the design was produced (process integrity)

The artwork is not AI-generated imagery and contains no AI artifacts. It is
generated as **clean vector geometry** by the toolkit in `tools/`
(`build_artwork.py` → `build_production.py` → `build_mockups.py` →
`build_docs.py`), which means:

* every shape is a mathematically defined arc, arch, ring, bar or node;
* type is real type, shaped with HarfBuzz from open-licence fonts
  (Space Grotesk, JetBrains Mono, Anton) and **converted to outlines**;
* the official logos are imported from the brand SVG files and only ever
  transformed rigidly;
* the package regenerates deterministically from source — edit a parameter,
  rebuild, and every deliverable (SVG, PDF, EPS, separations, PNG, TIFF, PSD,
  mockups, QC report) updates consistently.

See `docs/06-print-production-spec.md` for the full production specification and
`docs/09-deliverables-manifest.md` for every shipped file with hashes.
