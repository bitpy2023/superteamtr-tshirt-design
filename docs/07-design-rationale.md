# 07 · Design rationale (English)

**Design:** *ARENA PROTOCOL* — SuperteamTR back print + front chest mark
**Build:** 320 × 400 mm back print, 90 × 104 mm front mark, 40 mm sleeve mark,
64 × 26 mm neck label

---

## 1. How it references a futuristic Colosseum / crypto-expow atmosphere

The Colosseum is used as **architecture, not decoration**. The main graphic is a
plan view (top-down) of a two-tier arcade ring: 24 arched bays on the main tier,
16 on the second, four cardinal gates, an arena floor with seating spokes, a
gate rail and a central arena. That is the structural DNA of the Colosseum —
an arcade wall surrounding a fighting floor — rebuilt in pure geometry with no
stone, ruin, column ornament or gladiator reference.

The "futuristic expo" half comes from the same drawing: the arcade is wired like
a network (a dashed signal band with 12 node capsules and leaders), measured
like an engineering sheet (a 72-tick telemetry ring, dimension marks, read-out
bars) and stamped like an event artefact (Istanbul coordinates, `ISTANBUL · TR`,
`CONNECT. CREATE. SHIP.`). Up close it is technical data; from five metres it is
an arena. That double reading is the atmosphere the brief asked for: a
competition floor on expo day, seen from the broadcast camera.

## 2. How it represents SuperteamTR

Three moves, in reading order:

1. The arena *is* the Superteam idea — a place where builders gather, compete
   and ship together, with one builder-mark highlighted on the floor in brand
   red (the "player" marker).
2. The **official SuperteamTR lockup** (monogram with crescent and star +
   `superteam türkiye` wordmark) is the largest brand shape on the print,
   sitting directly under the arena as its signature.
3. The tagline `THE ARENA FOR BUILDERS` states the promise in words for anyone
   meeting the community for the first time, and `CONNECT. CREATE. SHIP.`
   closes the print with the community's verb sequence.

## 3. How Solana is integrated

* The **official Solana logomark** is placed at the exact mathematical centre of
  the arena inside a white "core coin" with a red hairline ring. It is the
  protocol at the middle of the ring — literally the thing being built on.
* The **official Solana logotype** (mark + wordmark) anchors the bottom of the
  print, offset from the SuperteamTR lockup so both brands get their own space
  and neither is subordinate.
* The Solana **purple → green gradient** appears where the brand itself defines
  it (inside the logomark), and the eco-system colours purple / teal are also
  used as print inks — so the shirt is Solana-native without a coin symbol,
  a price chart or a rocket.

## 4. How Turkish identity is represented

Deliberately quietly, per the brief:

* **Brand red.** The accent is the actual SuperteamTR red `#D6223B` (taken from
  the official mark), used only for gate keystones, the bridge terminus blocks,
  the index squares and the arena's gate rail — under 8 % of the ink area.
  No flag, no oversized crescent or star beyond what the official monogram
  already carries.
* **The bridge.** A dashed axis crosses the arena East–West, ending in two red
  terminus nodes: a compressed metaphor for Türkiye as the bridge between
  regions (and for cross-chain connection). It reads as a technical axis line
  first — the metaphor is there for people who look for it.
* **Place.** `ISTANBUL · TR` and the real coordinates `41.0082° N / 28.9784° E`
  are printed as data in the header row and repeated on the neck label: a
  location stamp, not a souvenir.

Nothing in the design is tourist-facing: there is no map outline, no tulip, no
evil eye, no mosque silhouette, no "Turkish" ornament pattern.

## 5. Why it is wearable

* One dominant idea per view (arena on the back, emblem on the chest) — never
  a collage.
* Washed black garment, four inks, generous negative space: the shirt works with
  denim, tech-wear, a hoodie underlayer or a blazer at a pitch.
* The arena's arcade bays are *open* (background shows through), so the print
  stays light on fabric and does not build a solid ink block on the chest/back.
* Type is small and technical where it is decorative, and large only where it is
  a message (`THE ARENA FOR BUILDERS`), so the shirt never looks like a
  conference badge.

## 6. Why it is practical to print

* Every shape is a **filled vector path** — no strokes, filters, textures,
  blends or opacity stacks.
* Line weights: minimum 0.35 mm hairlines, 0.42 mm ticks, 0.9 mm arcade walls;
  smallest type 8 pt. Above the thresholds where screen printing, DTG, DTF and
  embroidery fall apart.
* Deliberate **ink hierarchy**: white base (union plate) → red accent → purple →
  teal; 4 inks for the hero run, with a documented 2-ink build and a 1-ink
  fallback for every garment colour.
* The gradient only exists inside the official Solana logomark, and it has a
  hard-stop two-band screen-print substitute (no continuous-tone fade on press).
* Print geometry is garment-safe: 320 × 400 mm centred leaves ≥ 25 mm to every
  seam on a size-L tee; nothing crosses the collar rib or a shoulder seam.

## 7. How it remains original

* Every element was generated from primitive geometry by the toolkit in
  `tools/` (`svgutil.py` → `build_artwork.py`): arcs, rings, arches, bars,
  nodes, ticks. No artwork, poster, NFT, hackathon graphic or Colosseum
  illustration was traced, copied or imitated, and no AI raster imagery is used
  anywhere in the package — the files are deterministic vector geometry.
* The only third-party assets are the **official brand logos**, imported from
  the brands' own SVG files and used under a rigid transform only (uniform
  scale + translation), with hashes recorded in every artwork header and in the
  `*.placements.json` sidecars.
* The layout logic (arcade tiers + network + telemetry + dimension marks) is a
  construction specific to this brief; the same code can be re-run with
  different parameters (bay count, node count, palette) to produce a
  distinguishable family for future drops.

## 8. What to check before the run

`docs/08-quality-control.md` — 22 automated checks over the shipped files
(logo provenance, outlined type, English-only text, one/two/colour builds,
separations, resolution, mockup scale) plus four human sign-off items: brand
approval of the logo files, Pantone draw-downs, a physical print proof, and the
gradient-build decision for the press run.
