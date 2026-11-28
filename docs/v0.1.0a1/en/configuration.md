# Configuration

## gdproject.toml

Project configuration file, similar to `pyproject.toml` / `Cargo.toml`.

```toml
[project]
name = "my-game"
version = "0.1.0"
godot = ">=4.7.0"
license = "MIT"

[dependencies]
limbo-ai = ">=1.5.0"
phantom-camera = "^4.3.0"

[dev-dependencies]
gdunit4 = "^1.0.0"

[scripts]
test = "godot --headless --script res://tests/run_tests.gd"
```

## Version Constraints

| Syntax | Meaning | Example |
|--------|---------|---------|
| `1.5.0` | Exact version | `limbo-ai = "1.5.0"` |
| `^1.5.0` | Compatible update | `>=1.5.0, <2.0.0` |
| `~1.5.0` | Patch update | `>=1.5.0, <1.6.0` |
| `>=1.0.0` | Minimum version | `>=1.0.0` |
| `*` | Any version | `limbo-ai = "*"` |

## Files

| File | Purpose |
|------|---------|
| `gdproject.toml` | Project config and dependencies |
| `gdpm.lock` | Lock file for reproducible installs |
| `tag.gdpm` | Tracks which addon belongs to which plugin |
| `.engines-conf.json` | Project engine configuration |
| `gdpm-local/` | Packed local plugins |

## User directory (~/.gdpm)

All of gdpm's runtime data lives in a single directory:

| Path | Purpose |
|------|---------|
| `~/.gdpm/config.toml` | Global configuration (see below) |
| `~/.gdpm/cache/` | Download cache — the default location, relocatable via `cache_dir` |
| `~/.gdpm/engines/` | Installed Godot engines (`gdpm godot install`) |
| `~/.gdpm/local-engines.json` | Engines registered manually with `gdpm godot add` |

- Config files from older installs (the platformdirs location) migrate here automatically on the first run.
- Uninstalling gdpm removes only the executable and the PATH entry — everything under `~/.gdpm` is kept.
- `cache/` is safe to delete at any time (files are re-downloaded on demand); the rest is worth keeping.
- Changing `cache_dir` only redirects **future** downloads — existing files are **not** moved. To keep them, move them yourself (`mkdir -p ~/gdpm-cache && mv ~/.gdpm/cache/* ~/gdpm-cache/`); the old directory is never read or cleaned again.

## Global configuration

`~/.gdpm/config.toml` holds machine-wide defaults. Prefer editing it through the CLI:

```bash
gdpm config set parallel_downloads 8      # download concurrency (1-32)
gdpm config set default_engine steam-godot@4.7-stable
gdpm config set cache_dir "~/gdpm-cache"   # ~ is expanded; empty value resets
gdpm config set language zh                # help language: en / zh
gdpm config open                           # open the config directory
```

The file itself:

```toml
[defaults]
godot_path = "godot"
addons_dir = "addons"
parallel_downloads = 4
default_engine = ""

[store]
base_url = "https://store.godotengine.org/api/v1"

[cache]
dir = ""

[ui]
language = "en"
```

`gdpm config set` manages four keys: `parallel_downloads`, `default_engine`,
`cache_dir` and `language` (pass an empty value to reset to the default).
`godot_path`, `addons_dir` and `store.base_url` appear in the file but are
reserved — gdpm does not consume them yet.
