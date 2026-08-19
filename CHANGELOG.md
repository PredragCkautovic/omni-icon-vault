# Changelog

## 4.1.1 — Installer reliability hotfix

- Fix Bootstrap Icons 1.13.1 release-layout detection and add an SVG-only indexing fallback.
- Add automatic self-healing for stale/corrupt required source caches.
- Fetch Phosphor Core 2.1.1 from its published npm package instead of a non-existent GitHub tag.
- Add `.tar.gz`/`.tgz` extraction support.
- Ensure CLI integration is reached after recoverable source-cache failures.


## 4.1.0 — Workspace UI upgrade

- Rebuilt the local browser as an API-driven, paginated icon workspace.
- Added category, pack and representation filters plus relevance/name/pack sorting.
- Added compact, comfortable and large grid-density modes.
- Added dark, light and system-aware themes.
- Added Favorites and Recently Used views.
- Added a detail drawer with live preview size/color/background controls, download actions and project-manifest copying.
- Added search aliases for common icon vocabulary.
- Added `/api/stats`, `/api/batch` and `/api/random`; expanded `/api/search` with pagination, sort, format filters and optional previews.
- Updated the Figma plugin with faster preview loading, favorites, format filters and a selected-icon panel.
- Sanitized custom SVGs before browser/Figma indexing.
- Fixed duplicate `README-FIRST.txt` entries in generated release archives.
- Expanded the automated test suite for the new browser/API behavior.

## 4.0.0 — Cross-platform stable release

- Replaced Linux-only installation dependencies with a Python standard-library installer.
- Added Windows, macOS and Linux launch/install/uninstall entry points.
- Added per-user font installation on all three platforms.
- Added cross-platform server lifecycle and clipboard handling.
- Added `omni-icons open`, `start`, `stop`, `status`, `doctor` and `--version`.
- Added cross-platform desktop/login integration.
- Added GitHub-ready repository metadata, CI, release automation, tests and release packaging.
- Hardened archive extraction against path traversal.
- Kept the v3 browser, Figma plugin, favicon collector, custom SVG support and design-to-code exports.
- Updated Simple Icons pin to 16.28.0 and Lucide pin to 1.29.0.

## 3.0.0

- Added mega icon packs, favicons and custom SVG indexing.

## 2.0.1

- Added Figma localhost integration fix.

## 2.0.0

- Added canonical IDs, local API and design-to-code pipeline.
