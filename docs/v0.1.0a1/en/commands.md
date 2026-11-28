# Commands

## Project

| Command | Description | Options |
|---------|-------------|---------|
| `gdpm init` | Initialize a new gdpm project (auto-detects settings) | — |
| `gdpm create [name]` | Create a new Godot project (interactive) | `-o, --open`, `-y, --yes` |
| `gdpm sync` | Sync addons/ to lock file state | `--frozen`, `--dry-run` (`--check`), `--no-cache` |
| `gdpm lock` | Generate or update lock file | `--check` |
| `gdpm list` | List installed plugins | `--json` |
| `gdpm status` | Show plugin status and available updates | `--json` |

## Dependencies

| Command | Description | Options |
|---------|-------------|---------|
| `gdpm add <plugin>` | Add plugins to the project | `--dev`, `--local` |
| `gdpm remove <plugin>` | Remove plugins | `-r, --recursive` |
| `gdpm update` | Update plugins to newer versions | `--latest`, `--dry-run` (`--check`) |
| `gdpm search <query>` | Search Godot Asset Store | `-n, --limit`, `--sort`, `--all`, `--json` |
| `gdpm info <plugin>` | Show plugin details | — |
| `gdpm cache info` | Show cache size and location | — |
| `gdpm cache clean` | Clean all cached files | `-y, --yes` |
| `gdpm export` | Export plugins to zip archive | `-o, --output` |
| `gdpm import` | Import plugins from zip archive | — |

## Engine

| Command | Description | Options |
|---------|-------------|---------|
| `gdpm godot list` | List installed Godot engines | `-V, --version`, `-a, --all`, `-id` |
| `gdpm godot list -r` | List available versions from GitHub | `-p, --page`, `-a, --all` |
| `gdpm godot install <ver>` | Install a Godot engine | `--csharp` |
| `gdpm godot uninstall <ver>` | Uninstall a Godot engine | — |
| `gdpm godot add <path>` | Add a local Godot engine | `-n, --name` |
| `gdpm godot remove <name>` | Remove a local engine | — |
| `gdpm godot use <id>` | Set project engine | — |
| `gdpm godot info` | Show current engine info | — |
| `gdpm godot open` | Open Godot editor | `--run`, `--path` |
| `gdpm godot default <id>` | Set default engine | `--unset` |

## Configuration

| Command | Description | Options |
|---------|-------------|---------|
| `gdpm config set <key> <value>` | Set a global configuration key | `parallel_downloads`, `default_engine`, `cache_dir`, `language` |
| `gdpm config open` | Open the directory containing the global config | — |

## Common Options

| Option | Description |
|--------|-------------|
| `-y, --yes` | Skip all confirmation prompts |
| `-V, --version` | Show version |
| `-h, --help` | Show help |
| `-a, --about` | Show about banner (version, repository, contributors) |
| `--completion <zsh\|bash\|fish>` | Generate a shell completion script |
