# Engine Management

GDPM can manage Godot engine installations alongside plugins.

## Install from GitHub

```bash
# Install latest 4.7 stable
gdpm godot install 4.7

# Install specific version
gdpm godot install 3.6.2-stable

# Install C# version
gdpm godot install 4.7 --csharp
```

## Add local engine

```bash
# macOS
gdpm godot add /Applications/Godot.app

# Linux
gdpm godot add /usr/local/bin/godot

# With alias
gdpm godot add /path/to/Godot --name 4.7-custom
```

## List engines

```bash
# Installed engines
gdpm godot list

# Available versions from GitHub
gdpm godot list -r

# Compact ID view
gdpm godot list -id
```

## Set engine for project

```bash
gdpm godot use gdpm-godot@4.7-stable
```

This writes `.engines-conf.json` in the project root.

## Set default engine

```bash
# Set fallback for projects without explicit config
gdpm godot default steam@4.7-stable

# Show current default
gdpm godot default

# Remove default
gdpm godot default --unset
```

## Open Godot

```bash
# Open editor
gdpm godot open

# Run project
gdpm godot open --run
```

## Engine ID format

Engine IDs use `Name@Version` format:

- `gdpm-godot@4.7-stable` — Downloaded engine
- `steam@4.7-stable` — Local engine (added via `gdpm godot add`)
