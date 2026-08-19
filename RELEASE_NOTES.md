# Omni Icon Vault 4.1.2

### Final UI polish
- Sticky filters and visible active copy-capability indicator.
- Capability badges and explicit copy hints on icon cards.
- Responsive Copy/Sort controls remain available on phones.
- Skeleton loading, refined empty states, and improved card/detail interactions.
- Detail drawer now shows available copy capabilities and its primary action follows the active copy mode.

This patch makes the Web UI Copy selector behave as a true filter. Selecting SVG, Glyph, HTML, or CSS immediately narrows the grid to icons that actually support that copy format, including Favorites and Recent views. The local search API now accepts `capability=` and returns capability metadata for consistent pagination and filtering.



### Sidebar polish

The sidebar now uses one consistent monochrome outline icon system across categories and every icon pack, replacing mixed glyphs/monograms/dots with aligned, accessible SVG marks.
