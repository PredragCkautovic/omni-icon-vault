# Adding an icon source

A public source should satisfy all of these:

1. The icon assets are legally usable/redistributable for this aggregation model.
2. The source has a stable release/tag that can be pinned in `sources.json` when possible.
3. The parser can verify that a real local asset exists before adding an index item.
4. Its license and trademark caveats are documented in `THIRD_PARTY_NOTICES.md`.

## Steps

1. Add a download entry to `sources.json`.
2. Add source metadata to `SOURCE_INFO` in `tools/build-index.py`.
3. Add a parser in `tools/build-index.py` that calls `add()` / `vector_item()`.
4. Add the parser to the build sequence.
5. Add a regression fixture/test.
6. Run `python tools/build-index.py` against a real downloaded source before release.

Do not add paid packs, scraped proprietary assets, or sources whose terms prohibit redistribution or building a competing icon library.
