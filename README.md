# Omni Icon Vault 4.0

**One local icon library for Figma, websites and code — on Windows, macOS and Linux.**

Omni Icon Vault combines open icon packs, developer glyphs, brand marks, website favicons and your own SVGs into one searchable local browser and one canonical-ID design-to-code pipeline.

## What it includes

- Local Font-Awesome-style browser with search, filters and favorites
- Figma development plugin that inserts SVGs as editable vectors
- Font Awesome Free, Nerd Fonts Symbols, Bootstrap Icons, Material Symbols and Tabler Icons
- Simple Icons, Lucide, Heroicons, Phosphor, Iconoir, Ionicons, Octicons, Devicon and Fluent UI System Icons
- Real website favicon collection (`omni-icons favicon add example.com`)
- Your own SVG library in `custom-icons/`
- CLI export to SVG, HTML, CSS, JSON, React, Vue and Svelte
- Project manifests (`omni-icons.json`) and deterministic lock files
- Local API on `http://localhost:17836`
- Cross-platform installers and launchers

The repository does **not** commit downloaded third-party icon archives. The installer fetches pinned upstream sources into `vendor/` on the user's computer and preserves upstream license files when available.

## Requirements

- Python 3.10 or newer
- Internet access during the first install/update
- Figma desktop app if you want the Figma plugin

No pip packages, Node.js, curl, unzip or package manager are required for Omni itself.

## Install

### Windows 10/11

1. Download and extract the release ZIP.
2. Double-click `INSTALL_WINDOWS.cmd`.
3. Open a **new** terminal after install so the new `omni-icons` PATH entry is visible.

PowerShell users can run:

```powershell
.\INSTALL_WINDOWS.ps1
```

### macOS

Double-click `INSTALL_MAC.command`, or run:

```bash
./INSTALL_MAC.command
```

### Linux

```bash
chmod +x INSTALL_LINUX.sh
./INSTALL_LINUX.sh
```

The installer downloads icon sources, builds the local index, installs the icon fonts for your user account, creates a launcher/CLI integration and starts the local browser/API.

Useful installer options:

```text
--core-only        install only the five core packs
--refresh          redownload pinned upstream assets
--no-fonts         skip desktop font installation
--no-integration   skip PATH/menu/startup integration
--no-autostart     do not start Omni automatically at login
--no-start         do not start the local server after install
```

## Open and search

```bash
omni-icons open
omni-icons search camera
omni-icons search github --source kind:brand
omni-icons search terminal --source kind:developer
```

Other useful commands:

```bash
omni-icons doctor
omni-icons status
omni-icons start
omni-icons stop
omni-icons show tabler:outline:camera
omni-icons copy tabler:outline:camera --format svg
```

## Figma

After installation:

1. Open Figma Desktop.
2. Open **Plugins → Development → Import plugin from manifest…**
3. Select `figma-plugin/manifest.json` from this repository.
4. Run **Omni Icon Vault Local** from Development plugins.

Search in the plugin and click an icon. SVG packs insert as editable vector nodes; supported raster favicons insert as image fills; Material/Nerd glyphs use the installed local fonts.

The Figma plugin talks only to the local Omni server at `http://localhost:17836`.

## Favicons

```bash
omni-icons favicon add github.com
omni-icons favicon add https://figma.com
omni-icons favicon list
omni-icons favicon refresh
omni-icons favicon remove github.com
```

Collected favicons stay local and are indexed with IDs such as:

```text
favicon:github.com
```

## Custom icons

Put SVG files anywhere under `custom-icons/`:

```text
custom-icons/
  automotive/engine.svg
  business/invoice.svg
  my-brand/logo-mark.svg
```

Then run:

```bash
omni-icons rebuild
```

## Design-to-code

Every icon has one canonical ID, for example:

```text
tabler:outline:camera
fontawesome:brands:github
simpleicons:brand:figma
favicon:example.com
custom:automotive:engine
```

Use the same ID in the browser, Figma and CLI.

Export directly:

```bash
omni-icons export tabler:outline:camera --format svg --out src/icons
omni-icons export tabler:outline:camera --format react --out src/components/icons
omni-icons export simpleicons:brand:github --format vue --out src/icons
```

Or create a project manifest:

```bash
omni-icons init .
# edit omni-icons.json
omni-icons sync
```

## Repository / GitHub publishing

This tree is ready to publish as a GitHub repository. It includes:

- MIT license for Omni code
- third-party notices
- contributing/security/code-of-conduct files
- cross-platform tests
- GitHub Actions CI on Ubuntu, Windows and macOS
- tag-driven release workflow
- release packaging script that generates source, Windows, macOS and Linux ZIPs plus SHA-256 checksums

See [`docs/PUBLISHING.md`](docs/PUBLISHING.md) and [`docs/RELEASING.md`](docs/RELEASING.md).

## Security model

- The local API binds to `127.0.0.1` only.
- Download archives are extracted with path-traversal checks.
- The favicon collector limits download size and sanitizes SVGs before storing them.
- Third-party source URLs are pinned to explicit releases/tags where the upstream project provides them.
- Material Symbols currently comes from Google's upstream `master` variable-font files because that repository does not publish a matching release asset; this floating source is documented in `sources.json`.

## Licensing and trademarks

Omni Icon Vault code is MIT licensed. Downloaded icon packs retain their own licenses. Brand marks and website favicons can also be protected by trademark/copyright rules even when distributed from an open-source icon repository. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) before redistributing brand assets.

## Uninstall

Windows:

```cmd
UNINSTALL_WINDOWS.cmd
```

macOS:

```bash
./UNINSTALL_MAC.command
```

Linux:

```bash
./UNINSTALL_LINUX.sh
```

Add `--purge-data` to remove downloaded `cache/` and `vendor/` data. Your `custom-icons/` and favicon registry are intentionally preserved.
