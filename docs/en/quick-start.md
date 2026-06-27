# Quick Start

## Initialize a project

```bash
cd my-godot-project
gdpm init
```

This creates `gdproject.toml` and `gdpm.lock`.

## Create a new project

```bash
gdpm create my-game
```

Interactive prompts guide you through project setup, Godot version, and engine selection.

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
