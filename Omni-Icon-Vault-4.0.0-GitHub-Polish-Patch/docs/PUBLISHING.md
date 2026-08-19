# Publishing Omni Icon Vault on GitHub

The repository is designed to be published without committing downloaded third-party icon archives, generated indexes, or user-collected favicon data.

## First repository publish

Authenticate with GitHub CLI:

```bash
gh auth login
gh auth status
```

Initialize and commit the source tree if needed:

```bash
git init
git add .
git commit -m "Omni Icon Vault 4.0.0"
git branch -M main
```

Create and push a new public repository:

```bash
gh repo create omni-icon-vault \
  --public \
  --source=. \
  --remote=origin \
  --push
```

For the canonical repository used by this release, the remote is:

```text
https://github.com/PredragCkautovic/omni-icon-vault.git
```

Verify:

```bash
git remote -v
git status
```

## Repository settings

Recommended GitHub settings:

- Enable **Issues** for bug reports and feature requests.
- Enable **Discussions** if you want community support/Q&A.
- Enable **Security → Private vulnerability reporting**.
- Protect `main` and require the **CI** workflow before merge.
- Keep GitHub Actions enabled for cross-platform validation and releases.

## Publish v4.0.0 — recommended automated path

Make sure the README/release polish is committed before creating the tag:

```bash
git add README.md RELEASE_NOTES.md docs/PUBLISHING.md
git commit -m "Polish README and release documentation"
git push origin main
```

Create and push the release tag:

```bash
git tag -a v4.0.0 -m "Omni Icon Vault 4.0.0"
git push origin v4.0.0
```

The included `.github/workflows/release.yml` then:

1. Tests Ubuntu, Windows, and macOS.
2. Verifies that the tag matches `VERSION`.
3. Builds source/Windows/macOS/Linux ZIPs.
4. Generates SHA-256 checksums.
5. Creates the GitHub Release using `RELEASE_NOTES.md`.

Watch the workflow:

```bash
gh run list --workflow release.yml --limit 5
gh run watch
```

Open the finished release:

```bash
gh release view v4.0.0 --web
```

## Manual fallback

Use this only if the automatic release workflow did not create a release.

Build the archives locally:

```bash
rm -rf dist
python scripts/build_release.py --dist dist
```

Make sure the tag exists on GitHub:

```bash
git tag -a v4.0.0 -m "Omni Icon Vault 4.0.0" 2>/dev/null || true
git push origin v4.0.0
```

Create the GitHub Release and upload all assets:

```bash
gh release create v4.0.0 \
  dist/Omni-Icon-Vault-4.0.0-source.zip \
  dist/Omni-Icon-Vault-4.0.0-windows.zip \
  dist/Omni-Icon-Vault-4.0.0-macos.zip \
  dist/Omni-Icon-Vault-4.0.0-linux.zip \
  dist/SHA256SUMS.txt \
  --verify-tag \
  --title "Omni Icon Vault 4.0.0" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

If a release already exists but is missing assets:

```bash
gh release upload v4.0.0 dist/Omni-Icon-Vault-4.0.0-*.zip dist/SHA256SUMS.txt --clobber
```

## What must never be committed

The `.gitignore` excludes runtime/generated data including:

- `vendor/` downloaded third-party icon trees
- `cache/` upstream archives
- generated browser icon indexes
- locally collected favicon files and registry
- installed-state/runtime data

This keeps the public repository small and prevents accidental publication of user-specific favicon data.
