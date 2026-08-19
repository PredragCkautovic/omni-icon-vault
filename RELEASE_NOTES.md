# Omni Icon Vault 4.1.0 — Workspace UI upgrade

Omni Icon Vault 4.1 turns the local browser into a faster, more complete icon workspace while keeping the same cross-platform installers, canonical IDs, Figma pipeline and design-to-code tooling introduced in 4.0.

## Highlights

- Completely redesigned responsive Web UI for large icon libraries.
- API-driven paginated search instead of loading the entire icon index into the browser page.
- Search ranking improvements plus useful aliases such as `gear → settings`, `trash → delete`, `photo → image` and `account → user`.
- Filter by UI / brand / developer category, individual source pack, and SVG / font / raster format.
- Sort by relevance, icon name or source pack.
- Compact, comfortable and large icon-grid density modes.
- Dark, light and system-aware themes.
- Favorites and recently-used icon views.
- Rich icon detail drawer with live size, color and background preview controls.
- One-click copy for canonical ID, best format, SVG, glyph, HTML, CSS and project-manifest entries.
- Direct SVG/raster download from the detail drawer.
- Faster Figma browser: search responses can include vector previews in one request instead of making a separate API request for every visible icon.
- Figma favorites and a dedicated selected-icon detail/insert panel.
- New local API endpoints: `/api/stats`, `/api/batch`, `/api/random`, paginated `/api/search`, format filtering and sorting.
- Custom SVG files are sanitized before they are injected into the local browser/Figma pipeline.
- Release builder no longer writes duplicate `README-FIRST.txt` entries.
- Expanded tests for the Web UI architecture, search pagination/filtering, stats and custom SVG sanitization.

## Upgrade from 4.0.0

Replace the application files with the 4.1.0 release and run the installer again for your platform. Existing downloaded icon sources can be reused when the installation directory/cache is preserved.

Then run:

```bash
omni-icons doctor
omni-icons open
```

For Figma, reopen the existing development plugin. The manifest path remains `figma-plugin/manifest.json` and the API remains on `http://localhost:17836`.

## First install

- Windows: `INSTALL_WINDOWS.cmd`
- macOS: `INSTALL_MAC.command`
- Linux: `./INSTALL_LINUX.sh`

Then run `omni-icons open` and, if needed, `omni-icons figma`.
