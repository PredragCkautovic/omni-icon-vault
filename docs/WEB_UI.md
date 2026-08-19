# Web UI

Omni Icon Vault 4.1 ships an API-driven local browser designed for large icon collections.

Open it with:

```bash
omni-icons open
```

The browser runs from the same localhost server used by the Figma plugin:

```text
http://localhost:17836/browser/index.html
```

## Search

Search works across icon names, labels, styles, source names, categories, URLs and indexed search terms.

Examples:

```text
camera
github
arrow left
python
settings
photo
account
```

The server also understands a small set of common aliases. For example, searching `gear` can match settings/cog icons and `trash` can match delete/bin icons.

Keyboard shortcuts:

| Shortcut | Action |
|---|---|
| `/` | Focus and select the search box |
| `Ctrl/Cmd + K` | Focus and select search |
| `Enter` in search | Open the first result |
| `Enter` on a focused card | Open icon details |
| `C` on a focused card | Copy using the selected Copy mode |
| `Esc` | Close details/sidebar |

## Filters

The left navigation filters by broad category or by one installed source pack.

The format chips filter the current result set to:

- SVG vectors
- font glyphs
- raster assets/favicons

Sorting can be changed between relevance, icon name and source pack.

## Favorites and recent icons

Favorites and recently-used icons are stored locally in the browser profile. No cloud account is used.

- Click the star on an icon card or in the detail drawer to favorite it.
- Copying or opening an icon places it in Recently Used.

## Detail drawer

The detail drawer provides:

- live preview size control
- preview color control
- dark/light/checkerboard backgrounds
- source/style/type/Unicode metadata
- canonical icon ID
- smart-format copy
- SVG, HTML, CSS and glyph copy actions
- project manifest entry copy
- SVG or raster download

## Grid density and theme

Three grid densities are available: Compact, Comfortable and Large.

The theme button cycles through Dark, Light and System. Preferences are stored locally in the browser profile.

## Performance model

Version 4.0 loaded the full generated `icon-data.js` into the page. Version 4.1 queries the local API in pages. This keeps initial browser load and DOM size bounded even when many icon packs are installed.

The browser requests vector previews only for the current page. Full icon records are fetched only when a detail/copy action needs them.
