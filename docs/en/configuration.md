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
