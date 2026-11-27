# FAQ

## gdpm vs manually downloading addons?

- One command instead of browsing the Asset Store
- Automatic dependency resolution
- Lock file for reproducible installs across team
- Version constraints (`^`, `~`, `>=`)

## Does GDPM require a custom registry?

No. GDPM uses the official [Godot Asset Store API](https://store.godotengine.org/api/v1/redoc) directly.

## How does plugin tracking work?

GDPM writes `tag.gdpm` files in each addon directory to track ownership:

```
addons/
  cogito/
    tag.gdpm    → store+philip-drobar/cogito
    plugin.cfg
  input_helper/
    tag.gdpm    → store+niceg/input_helper
```

## Can I use GDPM with Godot 3.x?

Yes. Version detection reads `project.godot` automatically and supports Godot 1.x through 4.x.

## Where is the cache stored?

Downloaded zips are cached in your platform's user cache directory (e.g. `~/.cache/gdpm` on Linux, `~/Library/Caches/gdpm` on macOS). Override it with `[cache] dir` in the global `config.toml`.
