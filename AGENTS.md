# AGENTS.md — gdpm

## Project Overview

gdpm is a dependency package manager for Godot plugins, similar to uv/npm/cargo. It uses the official Godot Asset Store API to discover and download plugins, with support for dependency management, lock files, and local plugins.

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
├── models/                  # Data models (zero dependencies)
│   ├── dependency.py        # Dependency model
│   ├── lock.py              # LockEntry model
│   ├── plugin.py            # Plugin, PluginDetail
│   └── version.py           # Version, VersionConstraint
├── config/                  # Configuration management
│   ├── project.py           # gdproject.toml reader/writer
│   └── global_config.py     # Global config (~/.config/gdpm/)
├── store/                   # Godot Asset Store API client
│   ├── protocol.py          # StoreProtocol interface
│   ├── client.py            # StoreClient (httpx async)
│   └── parser.py            # API response parsers
├── cache/                   # Local file cache
│   ├── protocol.py          # CacheProtocol interface
│   └── file_cache.py        # FileCache implementation
├── installer/               # Plugin installation
│   ├── protocol.py          # InstallerProtocol interface
│   └── manager.py           # PluginManager
├── lockfile/                # Lock file management
│   └── lock.py              # Read/write gdpm.lock
├── cli/                     # CLI commands (click)
│   ├── app.py               # Main entry, command group
│   ├── options.py           # Shared CLI options (yes_option)
│   ├── common.py            # Shared utilities
│   ├── init.py              # gdpm init
│   ├── add.py               # gdpm add (+ --local)
│   ├── remove.py            # gdpm remove
│   ├── sync.py              # gdpm sync
│   ├── lock.py              # gdpm lock
│   ├── list.py              # gdpm list
│   ├── search.py            # gdpm search
│   ├── info.py              # gdpm info
│   ├── update.py            # gdpm update
│   └── status.py            # gdpm status
└── utils/                   # Utility modules
    ├── checksum.py          # SHA256 checksum
    ├── godot.py             # Godot version detection
    ├── local.py             # Local plugin management
    ├── platform.py          # Platform detection
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
- Click for CLI framework

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

## Version System

| Format | Example | Meaning |
|--------|---------|---------|
| `x.y.z` | `0.0.3` | Stable release |
| `x.y.z.dev1` | `0.0.3.dev1` | Development |
| `x.y.za1` | `0.0.3a1` | Alpha |
| `x.y.zb1` | `0.0.3b1` | Beta |
| `x.y.zrc1` | `0.0.3rc1` | Release candidate |

Version is stored in:
- `pyproject.toml`: `version = "0.0.3b1"` (PyPI format)
- `src/gdpm/__init__.py`: `__version__ = "0.0.3b1"` + `__tag__ = "beta"`

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
python3 scripts/version.py 0.0.3 ""

# 2. Commit and push
git add -A && git commit -m "release: v0.0.3"
git push origin dev

# 3. Create PR and merge
gh pr create --base main --head dev
gh pr merge <PR> --squash --admin

# 4. Create release (triggers PyPI publish + build)
gh release create v0.0.3 --title "v0.0.3" --notes-file RELEASE_NOTES.md
```

## Important Notes

- `gdpm.lock` stores both online and local plugins
- Local plugins have `version = "local"` in lock file
- `tag.gdpm` files track which addon directories belong to which plugin
- `gdpm-local/` stores packed local plugins (committed to git)
- `addons/` is typically not committed (in .gitignore)
- Godot version detection supports 1.x through 4.x formats
