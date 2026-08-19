# Omni Icon Vault Local — Figma plugin

This is a local development plugin. It talks only to the Omni Icon Vault API at:

```text
http://localhost:17836
```

## One-time setup

1. Install Omni Icon Vault for your platform.
2. Start the local server:

   ```bash
   omni-icons figma
   ```

3. Open Figma Desktop and a design file.
4. Go to **Plugins → Development → Import plugin from manifest…**.
5. Select this folder's `manifest.json`.
6. Run **Omni Icon Vault Local** from Plugins → Development.

## v4.1 workflow

- Search all installed icon packs from the plugin.
- Switch between All, UI, Brands, Developer and Favorites.
- Filter by individual source pack and SVG/font/raster representation.
- Select an icon to preview it and see its canonical ID.
- Double-click an icon, or press **Insert**, to place it on the canvas.
- Choose the insertion size before inserting.
- Copy the canonical icon ID when you want the exact same asset in code.

SVG-backed icons become editable Figma vector nodes. Raster favicons become image-filled rectangles. Nerd Fonts and Material Symbols become text nodes using the local fonts installed by Omni.
