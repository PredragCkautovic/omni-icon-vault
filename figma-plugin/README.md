# Omni Icon Vault Local — Figma plugin

This is a private local development plugin. It talks only to the Omni Icon Vault API at `http://localhost:17836`.

## One-time Figma setup
1. Run `../INSTALL_PIPELINE.sh` so the local server is available.
2. Open Figma desktop / your compatible Figma desktop client.
3. Open a design file.
4. Go to **Plugins → Development → Import plugin from manifest…**.
5. Select this folder's `manifest.json`.
6. Run **Omni Icon Vault Local** from Plugins → Development.

Click an icon to insert it. SVG-backed packs become editable vector nodes. Nerd Fonts and Material Symbols become text nodes using the local fonts installed by Omni.
