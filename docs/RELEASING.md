# Releasing Omni Icon Vault

## Release checklist

1. Ensure `VERSION`, `manifest.json`, source metadata, and release notes agree.
2. Run the full test suite.
3. Build local archives once as a sanity check.
4. Commit and push `main`.
5. Create an annotated `vX.Y.Z` tag.
6. Push the tag and let GitHub Actions publish the release.
7. Verify release assets and checksums.

## Validate locally

```bash
python -m unittest discover -s tests -v
python -m compileall -q install.py uninstall.py omni.py tools scripts tests
rm -rf dist
python scripts/build_release.py --dist dist
sha256sum -c dist/SHA256SUMS.txt
```

On macOS, use `shasum -a 256` if `sha256sum` is unavailable. The CI/release workflow performs the authoritative cross-platform test run.

## Publish the current version

```bash
VERSION="$(cat VERSION)"

git status --short
git push origin main

git tag -a "v$VERSION" -m "Omni Icon Vault $VERSION"
git push origin "v$VERSION"
```

Watch the release workflow:

```bash
gh run list --workflow release.yml --limit 5
gh run watch
```

Inspect the published release:

```bash
gh release view "v$VERSION"
gh release view "v$VERSION" --web
```

## Manual release fallback

If the automated workflow fails before creating a release:

```bash
VERSION="$(cat VERSION)"
rm -rf dist
python scripts/build_release.py --dist dist

gh release create "v$VERSION" \
  dist/Omni-Icon-Vault-"$VERSION"-source.zip \
  dist/Omni-Icon-Vault-"$VERSION"-windows.zip \
  dist/Omni-Icon-Vault-"$VERSION"-macos.zip \
  dist/Omni-Icon-Vault-"$VERSION"-linux.zip \
  dist/SHA256SUMS.txt \
  --verify-tag \
  --title "Omni Icon Vault $VERSION" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

## Existing release, rebuilt assets

```bash
VERSION="$(cat VERSION)"
gh release upload "v$VERSION" dist/Omni-Icon-Vault-"$VERSION"-*.zip dist/SHA256SUMS.txt --clobber
```

Do not move an existing stable version tag to a different commit after users may have downloaded it. For post-release changes, increment the version and publish a new tag.
