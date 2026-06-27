# GDPM

A dependency package manager for Godot plugins, like uv/npm/cargo.

## Features

- **One command install** — `gdpm add limbo-ai` instead of manual downloads
- **Dependency management** — Automatic dependency resolution
- **Lock file** — `gdpm.lock` ensures reproducible installs across team and CI
- **Godot Asset Store** — Direct integration with the official store API
- **Version constraints** — Support for `^`, `~`, `>=` semver syntax
- **Godot engine management** — Install, manage, and switch Godot versions
- **Global cache** — Shared cache across projects, saves disk space

## Quick Start

```bash
pip install godot-gdpm

# Initialize a project
gdpm init

# Add plugins
gdpm add limbo-ai
gdpm add phantom-camera

# Sync after git clone
gdpm sync
```

## Links

- [GitHub](https://github.com/Abyss-PlayerEG/godot-gdpm)
- [PyPI](https://pypi.org/project/godot-gdpm/)
- [Godot Asset Store](https://store.godotengine.org/)
- [Godot Asset Library](https://godotengine.org/asset-library/)
