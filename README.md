<div align="center">

[![English](https://img.shields.io/badge/English-blue?style=for-the-badge)](README.md) [![简体中文](https://img.shields.io/badge/简体中文-gray?style=for-the-badge)](README_CN.md)

</div>

---

# GDPM — Godot Dependency Package Manager

> A dependency package manager for Godot plugins, like uv/npm/cargo.

[![CI](https://github.com/Abyss-PlayerEG/godot-gdpm/actions/workflows/ci.yml/badge.svg)](https://github.com/Abyss-PlayerEG/godot-gdpm/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/godot-gdpm)](https://pypi.org/project/godot-gdpm/)
[![Python](https://img.shields.io/pypi/pyversions/godot-gdpm)](https://pypi.org/project/godot-gdpm/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/github/license/Abyss-PlayerEG/godot-gdpm)](LICENSE)

---

## Features

- **One command install** — `gdpm add limbo-ai` instead of manual downloads
- **Dependency management** — Automatic dependency resolution
- **Lock file** — `gdpm.lock` ensures reproducible installs across team and CI
- **Godot Asset Store** — Direct integration with the official store API
- **Version constraints** — Support for `^`, `~`, `>=` semver syntax
- **Template detection** — Automatically identifies project templates vs addons
- **Godot compatibility** — Checks plugin compatibility with your Godot version
- **Godot engine management** — Install, manage, and switch Godot versions
- **Global cache** — Shared cache across projects, saves disk space
- **Shell completion** — Tab completion for zsh, bash, fish

## Installation

```bash
pip install godot-gdpm
```

## Quick Start

```bash
# Initialize a project
gdpm init

# Create a new project
gdpm create my-game

# Add plugins
gdpm add limbo-ai
gdpm add phantom-camera
gdpm add --dev gdunit4

# Check status
gdpm status

# Sync addons (e.g., after git clone)
gdpm sync
```

## Commands

### Project

| Command | Description |
|---------|-------------|
| `gdpm init` | Initialize a new gdpm project |
| `gdpm create [name]` | Create a new Godot project (interactive) |
| `gdpm sync` | Sync addons/ to lock file state |
| `gdpm lock` | Generate or update lock file |
| `gdpm list` | List installed plugins |
| `gdpm status` | Show plugin status and available updates |

### Dependencies

| Command | Description |
|---------|-------------|
| `gdpm add <plugin>` | Add plugins to the project |
| `gdpm remove <plugin>` | Remove plugins |
| `gdpm update` | Update plugins to newer versions |
| `gdpm search <query>` | Search Godot Asset Store |
| `gdpm info <plugin>` | Show plugin details |

### Engine Management

| Command | Description |
|---------|-------------|
| `gdpm godot list` | List installed Godot engines |
| `gdpm godot list -r` | List available versions from GitHub |
| `gdpm godot install <ver>` | Install a Godot engine |
| `gdpm godot uninstall <ver>` | Uninstall a Godot engine |
| `gdpm godot add <path>` | Add a local Godot engine |
| `gdpm godot remove <name>` | Remove a local engine |
| `gdpm godot use <id>` | Set project engine |
| `gdpm godot info` | Show current engine info |
| `gdpm godot open` | Open Godot editor |
| `gdpm godot default <id>` | Set default engine |

### Cache

| Command | Description |
|---------|-------------|
| `gdpm cache info` | Show cache size and location |
| `gdpm cache clean` | Clean all cached files |

### Import/Export

| Command | Description |
|---------|-------------|
| `gdpm export` | Export plugins to zip archive |
| `gdpm import` | Import plugins from zip archive |

## Configuration

### gdproject.toml

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

### Version Constraints

| Syntax | Meaning | Example |
|--------|---------|---------|
| `1.5.0` | Exact version | `limbo-ai = "1.5.0"` |
| `^1.5.0` | Compatible update | `>=1.5.0, <2.0.0` |
| `~1.5.0` | Patch update | `>=1.5.0, <1.6.0` |
| `>=1.0.0` | Minimum version | `>=1.0.0` |
| `*` | Any version | `limbo-ai = "*"` |

## How It Works

gdpm uses the official [Godot Asset Store API](https://store.godotengine.org/api/v1) to discover and download plugins. It does **not** require a custom registry.

```
gdpm add limbo-ai
  → Search Godot Asset Store API
  → Download plugin zip
  → Extract to addons/
  → Write tag.gdpm for tracking
  → Update gdproject.toml + gdpm.lock
```

### Plugin Tracking

gdpm uses `tag.gdpm` files to track which addon directories belong to which plugin.

```
addons/
  cogito/
    tag.gdpm          → store+philip-drobar/cogito
    plugin.cfg
    ...
  input_helper/
    tag.gdpm          → store+philip-drobar/cogito
    ...
```

## Engine Management

gdpm can manage Godot engine installations:

```bash
# Install Godot 4.7
gdpm godot install 4.7

# Install C# version
gdpm godot install 4.7 --csharp

# Add local engine (e.g., Steam)
gdpm godot add "/path/to/Godot.app"

# Set engine for current project
gdpm godot use gdpm-godot@4.7-stable

# Open Godot editor
gdpm godot open
```

## CI/CD Integration

```yaml
# GitHub Actions
- name: Install Godot plugins
  run: |
    pip install godot-gdpm
    gdpm sync --frozen
```

## Development

```bash
# Clone the repository
git clone https://github.com/Abyss-PlayerEG/godot-gdpm.git
cd godot-gdpm

# Install dependencies
uv sync

# Run checks
python scripts/check.py

# Build executable
python scripts/build.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/new-feature`)
3. Commit your changes (`git commit -m "feat: add new feature"`)
4. Push to the branch (`git push origin feat/new-feature`)
5. Open a Pull Request

## License

GPL-3.0 License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Godot Engine](https://godotengine.org/) — The game engine
- [Godot Asset Store](https://store.godotengine.org/) — Official plugin store
- [uv](https://github.com/astral-sh/uv) — Inspiration for the CLI design
- [Rich](https://github.com/Textualize/rich) — Terminal formatting
- [Click](https://github.com/pallets/click) — CLI framework
- [Questionary](https://github.com/tmbo/questionary) — Interactive prompts
