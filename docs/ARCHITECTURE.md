# Architecture

```text
Pinned upstream sources -> install.py -> vendor/
                                  |
                                  v
                         tools/build-index.py
                                  |
                    browser/icon-data.json
                       /          |          \
                      v           v           v
               Local browser   Figma API    CLI/export
                      \           |           /
                       \----------+----------/
                          canonical icon IDs
```

`tools/omni_server.py` serves the browser and read-only icon API on loopback. `tools/omni_cli.py` handles search/export/project sync. `tools/favicon_manager.py` collects explicitly requested website favicons. `custom-icons/` is indexed as a user-owned source.
