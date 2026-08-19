# Omni Icon Vault 4.1.3

A small reliability and usability release that rolls the latest v4.1.2 UI fixes into a clean public build and hardens GitHub release publishing.

## Highlights

- Exact preview-size field now supports normal typing without clamping mid-entry.
- Preview slider and exact pixel field stay synchronized and persist the chosen size.
- Keeps the v4.1.2 capability filtering, stale-server recovery, sidebar icon polish, responsive controls, favorites/recent views, and improved detail drawer.
- Release workflow now normalizes `VERSION`, prints tag diagnostics, verifies generated archives, and treats reruns of an already-published release safely.

## Upgrade

Install from the platform release archive or update an existing source checkout:

```bash
git pull
python install.py
```

Then open Omni:

```bash
omni-icons open
```
