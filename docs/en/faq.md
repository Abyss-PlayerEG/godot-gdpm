# FAQ

## gdpm vs manually downloading addons?

- One command instead of browsing the Asset Store
- Automatic dependency resolution
- Lock file for reproducible installs across team
- Version constraints (`^`, `~`, `>=`)

## Does GDPM require a custom registry?

No. GDPM uses the official [Godot Asset Store API](https://store.godotengine.org/api/v1) directly.

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

Yes. GDPM supports Godot 3.x and 4.x. Version detection reads `project.godot` automatically.

## Where is the cache stored?

Global cache is in `~/.gdpm/cache/`. Use `gdpm cache info` to check size and location.
