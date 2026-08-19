# Omni Icon Vault 4.0.0

The first stable, GitHub-ready release of **Omni Icon Vault** for Windows, macOS, and Linux.

Omni combines multiple icon ecosystems, real website favicons, and custom SVGs into one local searchable library. A single canonical icon ID can be used in the browser, Figma plugin, CLI, local API, and generated React/Vue/Svelte/SVG code.

## Highlights

- Cross-platform installers for **Windows, macOS, and Linux**.
- Search across **14 upstream icon sources**, plus collected favicons and custom SVGs.
- Local **Figma development plugin** with editable SVG vector insertion.
- Canonical icon IDs shared across design and code.
- Export to **React, Vue, Svelte, SVG, HTML, CSS, JSON, glyph, and asset** formats.
- Real website favicon collection with SVG sanitization.
- Local browser + API on `http://localhost:17836`.
- User-level font installation for supported font-backed packs.
- `omni-icons init` / `omni-icons sync` project manifests and lock hashes.
- Cross-platform Python installer with no Node.js requirement.
- GitHub Actions CI for Ubuntu, Windows, and macOS.
- SHA-256 checksums for all packaged release archives.

## Downloads

Choose the archive for your platform from the release assets:

- `Omni-Icon-Vault-4.0.0-windows.zip`
- `Omni-Icon-Vault-4.0.0-macos.zip`
- `Omni-Icon-Vault-4.0.0-linux.zip`
- `Omni-Icon-Vault-4.0.0-source.zip`
- `SHA256SUMS.txt`

## First install

### Windows

Extract the Windows ZIP and run:

```text
RUN_ME_FIRST.cmd
```

### macOS

Extract the macOS ZIP and run:

```bash
./INSTALL_MAC.command
```

### Linux

Extract the Linux ZIP and run:

```bash
chmod +x INSTALL_LINUX.sh
./INSTALL_LINUX.sh
```

Then on any platform:

```bash
omni-icons doctor
omni-icons open
```

For Figma integration:

```bash
omni-icons figma
```

## Included source families

Font Awesome Free, Nerd Fonts Symbols, Bootstrap Icons, Material Symbols, Tabler, Simple Icons, Lucide, Heroicons, Phosphor, Iconoir, Ionicons, Octicons, Devicon, and Microsoft Fluent UI System Icons — plus local favicons and custom SVGs.

## Licensing note

Omni Icon Vault's own code is MIT-licensed. Third-party icon packs retain their original licenses. Brand marks and favicons can also be subject to trademark or brand-usage rules; see `THIRD_PARTY_NOTICES.md` before redistributing or using brand assets commercially.
