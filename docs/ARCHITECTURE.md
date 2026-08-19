# Architecture

```text
Pinned upstream sources ──> install.py ──> vendor/
                                      │
                                      ▼
                             tools/build-index.py
                                      │
                                      ▼
                             browser/icon-data.json
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                tools/omni_server.py        tools/omni_cli.py
                  localhost:17836            local files
                         │                         │
              ┌──────────┼───────────┐             │
              ▼          ▼           ▼             ▼
          Web UI      Figma UI   Local API     export/sync
              \          |           /             /
               \─────────┴───────────┴────────────/
                         canonical icon IDs
```

## Indexing

`tools/build-index.py` normalizes all supported icon packs into one JSON record format. Every record receives a stable canonical ID such as:

```text
tabler:outline:camera
simpleicons:brand:github
favicon:example.com
```

The generated index is local runtime data and is not committed to release bundles.

Custom SVGs are sanitized before they enter the generated index. Collected SVG favicons are sanitized by the favicon collector as well.

## Local server

`tools/omni_server.py` binds to the loopback interface and serves both the browser and a read-only icon API.

Important endpoints:

```text
GET /api/health
GET /api/stats
GET /api/sources
GET /api/search?q=camera&source=all&format=svg&sort=relevance&offset=0&limit=120&include=preview
GET /api/icon?id=tabler:outline:camera
GET /api/batch?ids=id1,id2,id3&include=preview
GET /api/random?source=kind:ui&format=svg
```

The v4.1 browser is API-driven. It no longer injects the entire icon database into the initial page, keeping DOM and JavaScript memory usage bounded as the library grows.

## Browser

`browser/index.html`, `browser/style.css` and `browser/app.js` implement the local workspace. Browser-only preferences such as theme, grid density, favorites and recent icons are stored in the browser profile via `localStorage`.

## Figma

The Figma development plugin uses the same localhost API and canonical IDs. Search responses may include SVG previews so the plugin can render a result page without issuing a separate request for every visible vector icon.

## CLI and exports

`tools/omni_cli.py` reads the same generated index directly for terminal search, copying, framework export and project manifest sync.

## Favicons and custom icons

`tools/favicon_manager.py` collects explicitly requested website favicons. `custom-icons/` is indexed as a user-owned local source.
