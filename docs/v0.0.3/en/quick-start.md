# Quick Start

## Initialize your project

If you already have a Godot project:

```bash
cd my-godot-project
gdpm init
```

This creates `gdproject.toml` and `addons/` in your project directory.

To start from scratch in a new directory:

```bash
gdpm init my-game --godot ">=4.2.0"
```

## Add plugins

```bash
gdpm add limbo-ai
gdpm add phantom-camera
gdpm add --dev gdunit4
```

## Check status

```bash
gdpm status
```

## Sync after git clone

```bash
gdpm sync
```

Installs all plugins from `gdpm.lock` — ensures consistent installs across team.

## In CI

```bash
gdpm sync --frozen
```

`--frozen` installs exactly what the lock file says, without re-resolving versions.
