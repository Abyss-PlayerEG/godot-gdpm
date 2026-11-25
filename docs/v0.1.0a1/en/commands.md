# Commands

## Project

| Command | Description |
|---------|-------------|
| `gdpm init` | Initialize a new gdpm project |
| `gdpm create [name]` | Create a new Godot project (interactive) |
| `gdpm sync` | Sync addons/ to lock file state |
| `gdpm lock` | Generate or update lock file |
| `gdpm list` | List installed plugins |
| `gdpm status` | Show plugin status and available updates |

## Dependencies

| Command | Description |
|---------|-------------|
| `gdpm add <plugin>` | Add plugins to the project |
| `gdpm add --local` | Pack local plugins into gdpm-local/ |
| `gdpm remove <plugin>` | Remove plugins |
| `gdpm update` | Update plugins to newer versions |
| `gdpm search <query>` | Search Godot Asset Store |
| `gdpm info <plugin>` | Show plugin details |
| `gdpm cache info` | Show cache size and location |
| `gdpm cache clean` | Clean all cached files |
| `gdpm export` | Export plugins to zip archive |
| `gdpm import` | Import plugins from zip archive |

## Engine

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

## Common Options

| Option | Description |
|--------|-------------|
| `-y, --yes` | Skip all confirmation prompts |
| `-V` | Show version |
| `-h` | Show help |
| `-i` | Show detailed info |
