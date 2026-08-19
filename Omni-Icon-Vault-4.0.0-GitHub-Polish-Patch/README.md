<div align="center">

# ◈ Omni Icon Vault

### One local icon library for **Figma, websites, apps, terminals, and design systems**.

Search thousands of UI, brand, developer, font, favicon, and custom SVG icons from one place — then use the **same canonical icon ID** in Figma and code.

[![CI](https://github.com/PredragCkautovic/omni-icon-vault/actions/workflows/ci.yml/badge.svg)](https://github.com/PredragCkautovic/omni-icon-vault/actions/workflows/ci.yml)
[![Latest Release](https://img.shields.io/github/v/release/PredragCkautovic/omni-icon-vault?display_name=tag&sort=semver)](https://github.com/PredragCkautovic/omni-icon-vault/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-supported-0078D6?logo=windows)](#windows)
[![macOS](https://img.shields.io/badge/macOS-supported-000000?logo=apple)](#macos)
[![Linux](https://img.shields.io/badge/Linux-supported-FCC624?logo=linux&logoColor=black)](#linux)

**[Download latest release](https://github.com/PredragCkautovic/omni-icon-vault/releases/latest)** · **[Figma setup](docs/FIGMA.md)** · **[CLI reference](docs/CLI.md)** · **[Contributing](CONTRIBUTING.md)**

</div>

---

## What is Omni Icon Vault?

Omni Icon Vault is a **local-first icon browser and design-to-code pipeline**. It combines multiple open icon ecosystems into a single searchable index and gives every icon a stable canonical ID.

Pick an icon once:

```text
tabler:outline:camera
```

Use that same ID across:

```text
                  Omni Icon Vault
                        │
        ┌───────────────┼───────────────┐
        │               │               │
     Browser          Figma            CLI
        │               │               │
        └───────────────┼───────────────┘
                        │
                  Canonical ID
                        │
          ┌─────────────┼─────────────┐
          │             │             │
        React          Vue          Svelte
          │             │             │
          └────── SVG / HTML / CSS ───┘
```

No more hunting for the same icon again when moving from mockup to implementation.

## Highlights

- **Fast local search** across UI, brand, developer, font, favicon, and custom icon sources.
- **Figma plugin** that inserts SVG-backed icons as editable vectors.
- **Design-to-code IDs** shared by the browser, Figma plugin, CLI, and generated project files.
- **React, Vue, Svelte, SVG, HTML, CSS, JSON, glyph, and asset export**.
- **Real website favicon collector** with local indexing and SVG sanitization.
- **Custom SVG library** — drop your own `.svg` files into `custom-icons/` and rebuild.
- **Local HTTP API** for integrations and tooling.
- **Cross-platform installers** for Windows, macOS, and Linux.
- **Local-first runtime** — after icon sources are installed, normal browsing/search does not require a cloud service.
- **Self-contained Python tooling** with no Node.js requirement.

## Icon sources

Omni currently knows how to index **14 upstream icon sources**, plus collected favicons and your own SVGs.

| Category | Sources |
|---|---|
| General UI | Font Awesome Free, Bootstrap Icons, Material Symbols, Tabler, Lucide, Heroicons, Phosphor, Iconoir, Ionicons, Fluent UI System Icons |
| Brands | Simple Icons, Font Awesome Brands, Ionicons brands |
| Developer | Nerd Fonts Symbols, Octicons, Devicon |
| Personal/local | Website favicons, `custom-icons/` |

Third-party sources are downloaded to the user's machine during installation instead of being committed into this repository. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for licensing notes.

> [!IMPORTANT]
> An open-source icon file does not automatically grant permission to use a company's trademark. Brand logos and collected favicons may be subject to separate trademark or brand-usage rules.

---

# Installation

## Requirements

- **Python 3.10 or newer**
- Internet connection for the first source download and when collecting/refreshing favicons
- Figma Desktop only if you want the local Figma plugin

Download the platform ZIP from the **[latest GitHub Release](https://github.com/PredragCkautovic/omni-icon-vault/releases/latest)**, extract it, and install.

### Windows

Double-click:

```text
RUN_ME_FIRST.cmd
```

or:

```text
INSTALL_WINDOWS.cmd
```

Then open a new terminal:

```powershell
omni-icons doctor
omni-icons open
```

### macOS

Run:

```bash
./INSTALL_MAC.command
```

Then:

```bash
omni-icons doctor
omni-icons open
```

If macOS blocks the downloaded script, open **System Settings → Privacy & Security** and allow it, or run it from Terminal.

### Linux

Run:

```bash
chmod +x INSTALL_LINUX.sh
./INSTALL_LINUX.sh
```

Then:

```bash
omni-icons doctor
omni-icons open
```

The installer uses user-level integration where possible. `systemd --user` is used when available, but is not required for the core application.

---

## Search from the terminal

```bash
omni-icons search camera
omni-icons search github --source kind:brand
omni-icons search python --source kind:developer
omni-icons search folder --source tabler
```

Inspect an icon:

```bash
omni-icons show tabler:outline:camera
```

Copy it:

```bash
omni-icons copy tabler:outline:camera --format svg
omni-icons copy fontawesome:solid:user --format html
omni-icons copy simpleicons:brand:github --format id
```

## Export to a project

```bash
omni-icons export tabler:outline:camera \
  --format react \
  --out src/components/icons
```

Supported export formats:

```text
asset  svg  html  css  json  react  vue  svelte
```

For repeatable projects:

```bash
cd my-project
omni-icons init .
# edit omni-icons.json
omni-icons sync
```

`omni-icons sync` generates the selected icons and records hashes in `omni-icons.lock.json`.

---

# Figma

Omni includes a local Figma development plugin.

Start Omni and print the plugin location:

```bash
omni-icons figma
```

Then in **Figma Desktop**:

1. Open **Plugins → Development → Import plugin from manifest…**
2. Select `figma-plugin/manifest.json` from your Omni installation.
3. Run **Omni Icon Vault Local** from Development plugins.
4. Search and click an icon to insert it.

SVG-backed icons are inserted as editable Figma vectors. Raster favicons are inserted as image-filled rectangles. Font-backed Nerd Font / Material Symbol entries use the locally installed fonts.

See **[docs/FIGMA.md](docs/FIGMA.md)** for troubleshooting.

---

# Favicons

Collect a real site's favicon into your local library:

```bash
omni-icons favicon add github.com
omni-icons favicon add https://figma.com
```

Manage them:

```bash
omni-icons favicon list
omni-icons favicon refresh
omni-icons favicon remove github.com
```

Collected favicons receive IDs such as:

```text
favicon:github.com
```

They become searchable in the browser, CLI, API, and Figma plugin.

---

# Your own SVG library

Drop SVGs anywhere under:

```text
custom-icons/
```

Subfolders are allowed:

```text
custom-icons/
├── automotive/
│   ├── engine.svg
│   └── brake-disc.svg
└── business/
    └── invoice.svg
```

Rebuild:

```bash
omni-icons rebuild
```

They become searchable entries with stable IDs based on their paths.

---

# Local API

Omni's browser and Figma plugin share the same local API at:

```text
http://localhost:17836
```

Useful endpoints:

```text
GET /api/health
GET /api/search?q=camera
GET /api/search?q=github&source=kind:brand
GET /api/icon?id=tabler:outline:camera
GET /api/sources
```

The server binds to the local machine; the Figma manifest only permits the Omni localhost endpoint.

---

# Useful commands

```bash
omni-icons --version
omni-icons doctor
omni-icons open
omni-icons start
omni-icons stop
omni-icons status
omni-icons figma
omni-icons update
omni-icons rebuild
```

Full command reference: **[docs/CLI.md](docs/CLI.md)**.

---

# Development

Clone the repository:

```bash
git clone https://github.com/PredragCkautovic/omni-icon-vault.git
cd omni-icon-vault
```

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

Compile-check the Python sources:

```bash
python -m compileall -q install.py uninstall.py omni.py tools scripts tests
```

Build local release archives:

```bash
python scripts/build_release.py --dist dist
```

The generated release directory contains source, Windows, macOS, Linux ZIPs, and `SHA256SUMS.txt`.

### Repository layout

```text
browser/          local icon browser
figma-plugin/     local Figma plugin
custom-icons/     user/custom SVG source folder
tools/            indexer, CLI, server, favicon manager
scripts/          release tooling
tests/            cross-platform regression tests
docs/             usage and contributor documentation
sources.json      upstream source definitions
install.py        cross-platform installer
omni.py           top-level CLI entry point
```

See **[CONTRIBUTING.md](CONTRIBUTING.md)** and **[docs/ADDING_SOURCES.md](docs/ADDING_SOURCES.md)** before adding another upstream pack.

---

# Releases

Releases are tag-driven. CI tests Windows, macOS, and Linux before a release is published.

```bash
git tag -a v4.0.0 -m "Omni Icon Vault 4.0.0"
git push origin v4.0.0
```

The release workflow builds:

```text
Omni-Icon-Vault-4.0.0-source.zip
Omni-Icon-Vault-4.0.0-windows.zip
Omni-Icon-Vault-4.0.0-macos.zip
Omni-Icon-Vault-4.0.0-linux.zip
SHA256SUMS.txt
```

See **[docs/RELEASING.md](docs/RELEASING.md)** for the complete release process.

---

# Security & privacy

Omni is designed around a local server and local icon index. User-collected favicon assets and generated runtime data are excluded from Git by default.

Please report security issues according to **[SECURITY.md](SECURITY.md)** rather than opening a public vulnerability issue.

---

# License

Omni Icon Vault's own source code is licensed under the **MIT License**. Third-party icon sets retain their original licenses and trademark restrictions.

- [LICENSE](LICENSE)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [licenses/NOTICE.txt](licenses/NOTICE.txt)

---

<div align="center">

**One icon search. One canonical ID. Design → Figma → code.**

If Omni Icon Vault is useful to you, consider starring the repository so other designers and developers can find it.

</div>
