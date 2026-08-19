# CLI reference

```text
omni-icons open
omni-icons start|stop|status|doctor
omni-icons search QUERY [--source SOURCE] [--format all|svg|font|raster] [--sort relevance|name|pack] [-n N] [--json]
omni-icons show ICON_ID
omni-icons copy ICON_ID --format smart|svg|html|css|glyph|asset|id|json
omni-icons export ICON_ID... --format asset|svg|html|css|json|react|vue|svelte --out DIR
omni-icons init [PATH]
omni-icons sync [omni-icons.json]
omni-icons favicon add|list|remove|refresh ...
omni-icons rebuild
```

Source selectors support exact source names and semantic categories:

```text
kind:ui
kind:brand
kind:developer
kind:favicon
```


## Search examples

```bash
omni-icons search camera --format svg
omni-icons search github --source kind:brand --sort name
omni-icons search python --source kind:developer --format svg -n 50
```
