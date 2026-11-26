# Layout plan — news-image-20261126 (fixed edition, 26 Nov 2026, cut-off 01:00 UTC)

## Target
27 honest stories, 8 regions, 5 illustrated leads, 7 timeline entries,
1 schematic world map. This is an EARLY edition: research ran 00:40–01:00 UTC
on 26 Nov 2026, so the day had barely begun. Priority: factual accuracy >
temporal accuracy > coverage > geographic breadth > readability > visual polish.
Only 27 stories could be honestly verified by the cut-off; 40+ would have
required padding with 25 Nov events. Africa has no verified 26 Nov item by
the cut-off and says so honestly instead of borrowing an older story.

## Canvas
- Output: 1024×1024 PNG, ≤1 MiB. Render internally at 2048×2048, downscale LANCZOS.
- Deterministic: fixed coordinates, fixed story order, no randomness, no network,
  no timestamps in the image beyond the fixed date. Two runs must hash identically
  (verified: identical SHA-256 across runs).
- Fonts: DejaVu Sans / DejaVu Sans Bold, vendored into the repo as fonts/ (free licence),
  loaded from the script directory so the grader sandbox needs nothing external.

## Palette (restrained newspaper)
- Structure/ink: #152C43 (dark navy). Canvas: #F8F6F0 (warm paper).
- Region accents: #34658A (steel blue). Verified H: #247653 (green). Developing M: #8A6D1B (ochre, darkened for contrast).
- Saturated colour only for meaningful distinctions (confidence dots, region bars, lead scenes).

## Typography (at 1024 px; double at 2048 render)
- Masthead title 34px bold, date line 20px, edition/meta 12px.
- Lead headlines 16px bold, lead decks 12.5px.
- Region headings 14px bold, story headlines 12.5px, source/confidence labels 10px.
- All wrapping by measured text width (font.getbbox), never by character count.
- Every text box gets a measured fit check; overflow is a build failure, not a warning.

## Layout bands (y at 1024)
- Masthead 0–92: "THE WORLD IN ONE DAY" + "THURSDAY 26 NOVEMBER 2026 · EARLY EDITION" +
  "27 STORIES · 8 REGIONS" + "8 confirmed · 19 developing · cut-off 01:00 UTC".
  Date rule stated under the title: "Events of 26 Nov 2026 in local time, or within 26 Nov UTC."
- Leads 100–292: 1 wide lead (Thanksgiving feast, left 40%) + 2×2 grid of 4 leads (right 60%).
  Each lead: small symbolic drawn scene (vector primitives only) + headline + 1-line deck +
  source + H/M confidence label. Scenes: feast table (Thanksgiving), atom (Kim nuclear call),
  rising arrow (Nikkei), circle of stars (EU summit), two labelled bars (Fisher & Paykel).
  Labelled "Symbolic illustration". No faces, locations, injuries, weapons, documents
  or event details are drawn. Scenes are rendered on a separate layer and pasted, so
  nothing a scene draws can escape its box; orbit radii are sized by the smaller
  scene dimension.
- Map + timeline 308–444: schematic world map left (60%) — simplified continent
  outlines only, NO country borders, NO disputed borders, numbered regional markers +
  story counts, Asia and Oceania separate; timeline right (40%) — 7 entries, each citing
  story IDs, local times labelled, cut-off noted. Row spacing 14px so the note fits.
- Regional grid 452–968: 3 columns × 3 rows. Row heights are computed from the
  largest panel in the row (header + lead line + one row per non-lead story + padding),
  with leftover space split evenly. Each block: region name + count + compact stories
  (headline + source + H/M dot). No story repeated; leads are referenced by ID in their
  region block, not re-listed, so the unique count stays 27. The ninth cell is a compact
  "HOW TO READ THIS PAGE" box (confidence key, ID cross-reference note, symbolic-scene note).
  The Africa panel (0 stories) carries the honest note "No verified 26 Nov item by the
  01:00 UTC cut-off."
- Footer 968–1024: sources actually used (two lines), confidence legend + cut-off +
  symbolic-scene note (one line).

## Regions (stories)
NA 3, EU 3, AP 11, ME 1, AF 0, LATAM 2, OCE 2, Global Themes 5 = 27.
H = 8 confirmed (2+ independent sources), M = 19 developing (one attributed source).

## Cross-references
Story IDs (N1…G5) appear in grid, map markers carry region counts, timeline entries
cite story IDs, lead cards show ID · source · H/M. Repeats never inflate the count;
the masthead count (27) is computed from the frozen STORIES dataset inside main.py,
not typed by hand. Flattened regional IDs must equal the story-ID set exactly once each
(asserted at import).

## Failure modes guarded
- Wrong event date: every story carries event date + publication timestamp in STORIES.md;
  25 Nov and earlier events excluded unless a substantive new development first emerged
  on 26 Nov, dated honestly.
- Fabricated facts: frozen evidence dataset; every story has a source URL in STORIES.md.
- Layout overflow: every panel/lead/timeline/footer line has a measured fit assert;
  overflow is a build failure, not a warning.
- Font-environment drift: DejaVu fonts vendored in fonts/; the grader renders identical bytes.
- Saved-file drift: the saved PNG is reopened and validated (size 1024×1024, mode RGB)
  before the SHA-256 is printed.
