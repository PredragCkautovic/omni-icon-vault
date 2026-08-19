# Omni Icon Vault 4.0.0 — Stable cross-platform release

This is the first GitHub-ready stable build of Omni Icon Vault for **Windows, macOS and Linux**.

## Highlights

- One local searchable library spanning UI icons, brand icons, developer glyphs, website favicons and custom SVGs.
- Figma development plugin using the same canonical icon IDs as the CLI and generated code.
- Cross-platform Python installer with no curl/unzip/tar/Node dependency.
- Per-user icon-font installation on Windows/macOS/Linux.
- React, Vue, Svelte, SVG, HTML, CSS and JSON export.
- `omni-icons open/start/stop/status/doctor/figma/update` lifecycle commands.
- Hardened archive extraction and sanitized SVG favicon collection.
- GitHub Actions CI matrix for Ubuntu, Windows and macOS.
- Automated tag-based GitHub Releases with source + Windows + macOS + Linux ZIPs and SHA-256 checksums.

## First install

Windows: `INSTALL_WINDOWS.cmd`

macOS: `INSTALL_MAC.command`

Linux: `./INSTALL_LINUX.sh`

Then run `omni-icons open` and `omni-icons figma`.
