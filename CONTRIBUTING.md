# Contributing

Contributions are welcome.

1. Fork the repository and create a focused branch.
2. Keep third-party downloaded assets out of Git (`vendor/` and `cache/` are ignored).
3. Use Python 3.10+ and standard-library code where practical so all supported platforms stay dependency-light.
4. Run `python -m unittest discover -s tests -v` and `python -m compileall -q .` before opening a pull request.
5. For new upstream icon sources, document the license/trademark considerations in `THIRD_PARTY_NOTICES.md` and add a pinned source entry in `sources.json`.
6. Do not add paid/proprietary icon packs or assets that prohibit redistribution/aggregation.

See `docs/ADDING_SOURCES.md` for source-adapter guidance.
