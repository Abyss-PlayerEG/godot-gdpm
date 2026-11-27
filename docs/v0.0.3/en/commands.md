# Commands

## Project

| Command | Description | Options |
|---------|-------------|---------|
| `gdpm init [name]` | Initialize a new gdpm project | `--godot`, `--license`, `--as-plugin`, `--force` |
| `gdpm sync` | Sync addons/ to lock file state | `--frozen`, `--dry-run`, `--no-cache` |
| `gdpm lock` | Generate or update lock file | `--check` |
| `gdpm list` | List installed plugins | `--outdated`, `--json` |
| `gdpm status` | Show plugin status and available updates | `--json` |

## Dependencies

| Command | Description | Options |
|---------|-------------|---------|
| `gdpm add <plugin>` | Add plugins to the project | `--dev` |
| `gdpm remove <plugin>` | Remove plugins | `-r, --recursive` |
| `gdpm update` | Update plugins to newer versions | `--latest`, `--dry-run` |
| `gdpm search <query>` | Search Godot Asset Store | `-n, --limit`, `--sort`, `--all`, `--json` |
| `gdpm info <plugin>` | Show plugin details | — |

## Common Options

| Option | Description |
|--------|-------------|
| `-V` | Show version |
| `-h` | Show help |
