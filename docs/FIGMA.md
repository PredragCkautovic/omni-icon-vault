# Figma integration

Omni's Figma plugin is a local development plugin. It does not require publishing to the Figma Community.

## Setup

1. Install Omni Icon Vault and start the local server.
2. Open Figma Desktop.
3. Open **Plugins → Development → Import plugin from manifest…**.
4. Select `figma-plugin/manifest.json`.
5. Run **Omni Icon Vault Local**.

The manifest permits only `http://localhost:17836`. The server itself binds to the loopback interface.

You can also run:

```bash
omni-icons figma
```

which starts the server and prints the manifest location.

## v4.1 plugin workflow

The plugin now provides:

- fast API-driven search
- UI / brand / developer / favorites tabs
- individual source-pack filtering
- SVG / font / raster filters
- insert-size control
- local Figma favorites
- a selected-icon preview panel
- direct Insert and Copy Icon ID actions
- double-click insertion from the result grid

Vector previews are returned with the search page when available, reducing the number of localhost requests needed to render a result set.

## Insertion behavior

- SVG-backed icons become editable Figma vector nodes.
- PNG/WebP/JPEG favicon assets become image-filled rectangles.
- Nerd Fonts / Material Symbols glyphs use their installed local fonts.

Each inserted node stores Omni plugin data including the canonical icon ID and source.

If a glyph font is missing, rerun the installer without `--no-fonts`, restart Figma completely and use:

```bash
omni-icons doctor
```

## Troubleshooting

If the plugin says the server is offline:

```bash
omni-icons start
omni-icons status
```

If Figma appears to use an older plugin UI after an upgrade, remove the development plugin once and re-import `figma-plugin/manifest.json`.
