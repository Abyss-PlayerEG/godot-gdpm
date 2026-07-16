# AGENTS.md — gdpm

## Project Overview

gdpm is a dependency package manager for Godot plugins, similar to uv/npm/cargo. It uses the official Godot Asset Store API to discover and download plugins, with support for dependency management, lock files, local plugins, and Godot engine management.

## Quick Reference

| Action | Command |
|--------|---------|
| Run (dev) | `uv run gdpm <command>` |
| Type check | `uv run mypy src/` |
| Lint | `uv run ruff check src/` |
| Format | `uv run ruff format src/` |
| All checks | `python3 scripts/check.py` |
| Update version | `python3 scripts/version.py <version> [tag]` |
| Install (editable) | `pip install -e .` |

## Project Structure

```
src/gdpm/
├── __init__.py              # Version and tag
├── __main__.py              # Entry point
├── constants.py             # Global constants (URLs, filenames)
├── models/                  # Data models (zero dependencies)
│   ├── dependency.py        # Dependency model
│   ├── lock.py              # LockEntry model
│   ├── plugin.py            # Plugin, PluginDetail
│   └── version.py           # Version, VersionConstraint
├── config/                  # Configuration management
│   ├── project.py           # gdproject.toml reader/writer
│   ├── global_config.py     # Global config (~/.config/gdpm/)
│   └── local_engines.py     # Local Godot engine management
├── store/                   # Godot Asset Store API client
│   ├── protocol.py          # StoreProtocol interface
│   ├── client.py            # StoreClient (httpx async)
│   ├── parser.py            # API response parsers
│   └── utils.py             # Store utilities
├── cache/                   # Local file cache
│   ├── protocol.py          # CacheProtocol interface
│   ├── file_cache.py        # FileCache implementation
│   └── index.py             # Cache index management
├── installer/               # Plugin installation
│   ├── protocol.py          # InstallerProtocol interface
│   └── manager.py           # PluginManager
├── lockfile/                # Lock file management
│   ├── lock.py              # Read/write gdpm.lock
│   └── utils.py             # Lock file utilities
├── resolver/                # Dependency resolver (placeholder)
│   └── __init__.py
├── cli/                     # CLI commands (click)
│   ├── app.py               # Main entry, command group, banner
│   ├── options.py           # Shared CLI options (yes_option)
│   ├── common.py            # Shared utilities (console, find_project_root)
│   ├── context.py           # CLI context management
│   ├── display.py           # Display utilities
│   ├── init.py              # gdpm init
│   ├── create.py            # gdpm create <name>
│   ├── add.py               # gdpm add <plugin> (+ --local)
│   ├── remove.py            # gdpm remove <plugin>
│   ├── sync.py              # gdpm sync
│   ├── lock.py              # gdpm lock
│   ├── list.py              # gdpm list
│   ├── search.py            # gdpm search <query>
│   ├── info.py              # gdpm info <plugin>
│   ├── update.py            # gdpm update <plugin>
│   ├── status.py            # gdpm status
│   ├── export.py            # gdpm export (-o backup.zip)
│   ├── import_cmd.py        # gdpm import <source>
│   ├── cache_cmd.py         # gdpm cache (info, clean)
│   └── godot.py             # gdpm godot (engine management)
└── utils/                   # Utility modules
    ├── checksum.py          # SHA256 checksum
    ├── download.py          # Download utilities
    ├── godot.py             # Godot version detection
    ├── install.py           # Installation utilities (get_install_type, get_platform)
    ├── local.py             # Local plugin management (LOCAL_DIR_NAME, tag_plugin)
    ├── path.py              # Path utilities (shorten_path)
    ├── platform.py          # Platform detection
    ├── tag.py               # Tag file management (scan_addons)
    ├── version.py           # Version normalization
    └── zip.py               # ZIP extraction
```

## Code Conventions

- Python 3.14, strict type hints (mypy strict mode)
- All modules use `from __future__ import annotations`
- No comments unless asked
- Protocol classes for dependency injection (store, cache)
- Async/await for API calls (httpx)
- Rich for terminal output (Console, Progress, Table)
- Click for CLI framework (GdpmCommand, GdpmGroup classes)

## Architecture Principles

### Module Independence

```
models ← no dependencies
  ↑
config / store / cache / lockfile ← depend only on models
  ↑
resolver ← depends on models + store (via Protocol)
installer ← depends on models + store + cache (via Protocol)
  ↑
cli ← composition root, depends on all modules
```

### Protocol-Based Design

All external services use Protocol classes:

```python
class StoreProtocol(Protocol):
    async def search(self, query: str) -> list[Plugin]: ...
    async def get_plugin(self, slug: str) -> PluginDetail: ...
```

This allows:
- Easy testing (mock the protocol)
- Swappable implementations
- Clear interfaces

## CLI Commands

### Project Commands

| Command | Description |
|---------|-------------|
| `gdpm init` | Initialize a new gdpm project |
| `gdpm create <name>` | Create a new Godot project |
| `gdpm sync` | Sync addons/ to lock file state |
| `gdpm lock` | Generate or update lock file |
| `gdpm list` | List installed plugins |
| `gdpm status` | Show plugin status and updates |

### Dependency Commands

| Command | Description |
|---------|-------------|
| `gdpm add <plugin>` | Add plugins to the project |
| `gdpm add --local` | Add local plugins |
| `gdpm remove <plugin>` | Remove plugins |
| `gdpm update <plugin>` | Update plugins to newer versions |
| `gdpm search <query>` | Search Godot Asset Store |
| `gdpm info <plugin>` | Show plugin details |
| `gdpm cache` | Manage global cache (info, clean) |
| `gdpm export` | Export plugins to zip archive |
| `gdpm import <source>` | Import plugins from zip archive |

### Engine Commands (`gdpm godot`)

| Command | Description |
|---------|-------------|
| `gdpm godot list` | List installed Godot versions |
| `gdpm godot list --remote` | List available versions from GitHub |
| `gdpm godot install <version>` | Install Godot engine |
| `gdpm godot uninstall <version>` | Uninstall Godot engine |
| `gdpm godot add <path>` | Add a local Godot engine |
| `gdpm godot remove <name>` | Remove a local Godot engine |
| `gdpm godot use <id>` | Set Godot engine for current project |
| `gdpm godot info` | Show current Godot engine configuration |
| `gdpm godot open` | Open Godot editor |
| `gdpm godot open --run` | Run the project |
| `gdpm godot default` | Show default engine |
| `gdpm godot default <id>` | Set default engine |
| `gdpm godot default --unset` | Remove default engine |

## Key Data Flow

### Plugin Installation

```
gdpm add limbo-ai
  → Search Store API for "limbo-ai"
  → Get publisher slug (e.g., "limofeus")
  → Download zip from GitHub Releases
  → Extract to addons/limbo-ai/
  → Write tag.gdpm in addon directory
  → Update gdproject.toml
  → Update gdpm.lock
```

### Local Plugin Management

```
gdpm add --local
  → Scan addons/ for untagged or local-tagged directories
  → Compute hash of each plugin directory
  → Compare with gdpm-local/.hashes
  → Pack changed plugins to gdpm-local/*.zip
  → Write { local = true } to gdproject.toml
  → Write { version = "local", source = "local" } to gdpm.lock
```

### Sync Flow

```
gdpm sync
  1. Sync local plugins (gdpm-local/*.zip → addons/)
  2. Sync online plugins (Store API → addons/)
```

### Export/Import Flow

```
gdpm export
  → Read gdproject.toml and gdpm.lock
  → Scan addons/ for installed plugins
  → Create manifest.json with plugin metadata
  → Pack local plugins to zip archive

gdpm import plugins.zip
  → Read manifest.json from zip
  → Install store plugins via StoreClient
  → Extract local plugins to addons/
  → Update gdproject.toml and gdpm.lock
```

### Engine Management Flow

```
gdpm godot install 4.7
  → Fetch release info from GitHub API
  → Download Godot binary for current platform
  → Verify SHA256 hash
  → Extract to ~/.gdpm/engines/4.7-stable/
  → Fix macOS permissions (xattr, chmod)

gdpm godot use gdpm-godot@4.7-stable
  → Write .engines-conf.json in project root
  → Set engine for gdpm godot open
```

## Version System

| Format | Example | Meaning |
|--------|---------|---------|
| `x.y.z` | `0.1.0` | Stable release |
| `x.y.z.dev1` | `0.1.0.dev1` | Development |
| `x.y.za1` | `0.1.0a1` | Alpha |
| `x.y.zb1` | `0.1.0b1` | Beta |
| `x.y.zrc1` | `0.1.0rc1` | Release candidate |

Version is stored in:
- `pyproject.toml`: `version = "0.1.0b1"` (PyPI format)
- `src/gdpm/__init__.py`: `__version__ = "0.1.0b1"` + `__tag__ = "beta"`

## Constants

Key constants defined in `constants.py`:

| Constant | Value | Description |
|----------|-------|-------------|
| `CONFIG_FILENAME` | `gdproject.toml` | Project config file |
| `LOCK_FILENAME` | `gdpm.lock` | Lock file |
| `TAG_FILENAME` | `tag.gdpm` | Plugin tag file |
| `LOCAL_DIR_NAME` | `gdpm-local` | Local plugins directory |
| `REPO_URL` | GitHub URL | Repository URL |
| `GITHUB_API_URL` | GitHub API URL | API endpoint |
| `GODOT_RELEASES_URL` | GitHub API URL | Godot releases endpoint |

## Testing

```bash
# All checks
python3 scripts/check.py

# Individual
uv run mypy src/
uv run ruff check src/
uv run ruff format --check src/
```

## Release Flow

```bash
# 1. Update version
python3 scripts/version.py 0.1.0 ""

# 2. Commit and push
git add -A && git commit -m "release: v0.1.0"
git push origin dev

# 3. Create PR and merge
gh pr create --base main --head dev
gh pr merge <PR> --squash --admin

# 4. Create release (triggers PyPI publish + build)
gh release create v0.1.0 --title "v0.1.0" --notes-file RELEASE_NOTES.md
```

## Important Notes

- `gdpm.lock` stores both online and local plugins
- Local plugins have `version = "local"` in lock file
- `tag.gdpm` files track which addon directories belong to which plugin
- `gdpm-local/` stores packed local plugins (committed to git)
- `addons/` is typically not committed (in .gitignore)
- Godot version detection supports 1.x through 4.x formats
- `gdpm godot` command manages local Godot engine installations
- `gdpm export`/`import` for project backup/restore
- `gdpm cache` for managing download cache
- `.engines-conf.json` stores per-project Godot engine configuration
- `~/.gdpm/engines/` stores downloaded Godot binaries
- `~/.gdpm/github_token.txt` stores GitHub API token (optional)
