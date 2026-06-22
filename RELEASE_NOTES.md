# Release Notes

## v0.0.2

### New Features

- **Godot Asset Store Integration** — Search, browse, and install plugins directly from the official Godot Asset Store API.
- **Dependency Management** — Automatic dependency resolution with `gdproject.toml` and `gdpm.lock`.
- **Version Constraints** — Support for semver syntax (`^1.0.0`, `~1.5.0`, `>=1.0.0,<2.0.0`).
- **Template Detection** — Automatically identifies project templates vs addons.
- **Godot Version Compatibility** — Checks plugin compatibility with your project's Godot version.
- **Plugin Tracking** — `tag.gdpm` system for tracking bundled plugin sub-packages.
- **Auto-detect Godot Version** — Reads `project.godot` to detect Godot version (supports 1.x through 4.x).

### CLI Commands

- `gdpm init` — Initialize a new gdpm project
- `gdpm add <plugin>` — Add plugins to the project
- `gdpm remove <plugin>` — Remove plugins
- `gdpm sync` — Sync addons/ to lock file state
- `gdpm lock` — Generate or update lock file
- `gdpm list` — List installed plugins
- `gdpm status` — Show plugin status and available updates
- `gdpm search <query>` — Search Godot Asset Store
- `gdpm info <plugin>` — Show plugin details
- `gdpm update` — Update plugins to newer versions

### Improvements

- Progress bars with download speed for plugin installations.
- Beautiful CLI help interface with rich formatting.
- Short options `-V` (version) and `-h` (help).
- Version tag support (dev, beta, alpha, rc, stable).
- PyPI-compatible version formats.

### Infrastructure

- GitHub Actions CI with mypy, ruff, and format checks.
- Multi-platform build workflow (Linux, macOS arm64/x64, Windows).
- PyPI publishing with trusted publishers.
- Code quality tools: mypy, ruff, vulture, deptry, pre-commit.
