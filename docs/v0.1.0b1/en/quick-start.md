# Quick Start

There are two ways to get started with GDPM.

## Option 1: Initialize an existing project

If you already have a Godot project:

```bash
cd my-godot-project
gdpm init
```

This creates `gdproject.toml` and `gdpm.lock` in your project directory.

## Option 2: Create a new project

Start from scratch with an interactive setup:

```bash
gdpm create my-game
```

This guides you through project name, Godot version, engine selection, and creates the project structure for you.

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
