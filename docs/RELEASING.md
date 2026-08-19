# Release process

1. Update `VERSION`.
2. Update `manifest.json`, `sources.json`, `CHANGELOG.md` and any user-visible version strings.
3. Run:

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python scripts/build_release.py
```

4. Inspect `dist/` and `dist/SHA256SUMS.txt`.
5. Commit the release changes.
6. Tag and push:

```bash
git tag v4.0.0
git push origin main --tags
```

The GitHub release workflow uses the same `scripts/build_release.py` file, so local and CI-generated archives follow the same rules.
