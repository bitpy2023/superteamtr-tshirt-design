# 10 · Brand assets, fonts and licensing

## Official brand assets (unmodified)

All logos in the artwork are the **official files supplied by the brands** — nothing
was redrawn, traced, distorted, stretched, re-coloured (except the allowed
monochrome/one-colour build), rotated or otherwise altered. They are embedded
into the artwork SVGs **as vector paths**, transformed rigidly (uniform scale +
translation) so brand proportions are preserved.

| asset | sha256 | source | notes |
|---|---|---|---|
| `superteamtr-lockup-horizontal.svg` | `41d38beb1fba2827` | [source](https://tr.superteam.fun/brand/tr-type.svg) | Official SuperteamTR lockup: ST monogram (with crescent + star) + “superteam türkiye” wordmark. Used unmodified; monochrome white build for print, and the brand red #D6223B is retained as an ink option. |
| `superteamtr-monogram.svg` | `aeb70c9069c3a96e` | [source](https://tr.superteam.fun/brand/w-logo.svg) | Official SuperteamTR monogram alone (used in concept 3 and the diagram sheet). |
| `superteamtr-mark-badge-red.svg` | `8c9a973af86ac645` | [source](https://tr.superteam.fun/favicon.svg) | Official SuperteamTR badge: red tile + monogram + crescent/star. Reference for brand red. |
| `solanaLogoMark.svg` | `3d3401109aa061de` | [source](https://solana.com/src/img/branding/solanaLogoMark.svg) | Official Solana logomark (three stacked parallelograms with the official purple→green gradient #9945FF → #14F195). |
| `solanaLogo-Logo.svg` | `missing` | [source](https://solana.com/src/img/branding/solanaLogo.svg) | Official Solana logotype: logomark + wordmark, horizontal lockup. |
| `solanaWordMark.svg` | `e785361bfb1f7d08` | [source](https://solana.com/src/img/branding/solanaWordMark.svg) | Official Solana wordmark. |
| `solanaVerticalLogo.svg` | `29923dcd00ff8c73` | [source](https://solana.com/src/img/branding/solanaVerticalLogo.svg) | Official Solana vertical lockup (supplied for completeness). |
| `solanaFoundationLogo.svg` | `8a0fec2e4d80bb24` | [source](https://solana.com/src/img/branding/solanaFoundationLogo.svg) | Official Solana Foundation logotype (supplied for completeness). |

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
| `Anton-Regular.ttf` | Anton | OFL-1.1 | `a4ba3a92350ebb03` | Display face for the tagline and headline lockups (outlined in every deliverable) |
| `SpaceGrotesk-VF.ttf` | Space Grotesk (variable, wght 300–700) | OFL-1.1 | `acad6de1fc93436f` | Secondary grotesque: body copy, measurements, wordmark lockups |
| `JetBrainsMono-VF.ttf` | JetBrains Mono (variable, wght 100–800) | OFL-1.1 | `48715a42ec242c21` | Technical micro-type: coordinates, telemetry, labels, index marks |

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
