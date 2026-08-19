# Omni Icon Vault 4.1.1 — Installer reliability hotfix

This patch fixes installation failures discovered on a real Arch Linux install of 4.1.0.

## Fixed

- Bootstrap Icons 1.13.1 is now discovered regardless of the release archive layout.
- Bootstrap can fall back to indexing its SVG files even when font metadata moves or is absent.
- Required source failures now trigger a targeted clean redownload instead of aborting immediately.
- Phosphor Core 2.1.1 now comes from the official published npm package; the previous GitHub `v2.1.1` archive URL does not exist.
- Added safe `.tar.gz`/`.tgz` extraction for npm package archives.
- A successful repaired installation continues to CLI/font/desktop integration, so `omni-icons` is installed normally.

## Upgrade

Pull 4.1.1 and rerun:

```bash
git pull
python install.py
omni-icons doctor
omni-icons open
```

The installer will reuse healthy caches and automatically redownload a required source if its indexed result is empty.
