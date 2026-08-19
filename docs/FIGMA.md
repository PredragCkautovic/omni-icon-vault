# Figma integration

Omni's Figma plugin is a local development plugin. It does not require publishing to the Figma Community.

## Setup

1. Install Omni Icon Vault and leave the local server enabled.
2. Open Figma Desktop.
3. Open **Plugins → Development → Import plugin from manifest…**.
4. Select `figma-plugin/manifest.json`.
5. Run **Omni Icon Vault Local**.

The manifest permits only `http://localhost:17836`. The server itself binds to the loopback interface.

## Insertion behavior

- SVG-backed icons become editable Figma vector nodes.
- PNG/WebP/JPEG favicon assets become image-filled rectangles.
- Nerd Fonts / Material Symbols glyphs use their installed local fonts.

If a glyph font is missing, rerun the installer without `--no-fonts`, restart Figma completely and use `omni-icons doctor`.
