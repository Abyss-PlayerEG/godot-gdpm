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
- **Godot engine management** — Install, manage, and switch Godot versions
- **Global cache** — Shared cache across projects, saves disk space

## Installation

```bash
pip install godot-gdpm
```

## Quick Start

```bash
# Initialize an existing project
gdpm init

# Or create a new project
gdpm create my-game

# Add plugins
gdpm add limbo-ai
gdpm add phantom-camera

# Sync after git clone
gdpm sync
```

## Documentation

- [Documentation](https://abyss-playereg.github.io/godot-gdpm/) — Full documentation
- [Godot Asset Store](https://store.godotengine.org/) — Official plugin store
- [Godot Asset Library](https://godotengine.org/asset-library/) — Community asset library

## License

GPL-3.0 License — see [LICENSE](LICENSE) for details.
