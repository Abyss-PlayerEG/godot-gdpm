# Release Notes

## v0.0.4

### New Features

- **Local Plugin Management** — `gdpm add --local` to pack local plugins into `gdpm-local/` with hash-based change detection.
- **Install Scripts** — Platform-specific install/uninstall scripts (macOS, Linux, Windows) included in release archives.
- **macOS Gatekeeper Bypass** — Install script automatically removes quarantine attributes.
- **Global `-y/--yes` Option** — Skip all confirmation prompts with `gdpm -y <command>`.
- **Common Options Display** — Help output shows shared options (`-h`, `-V`, `-y`).

### Improvements

- Auto-detect Godot version from `project.godot` (supports 1.x through 4.x).
- Unified version format (`__version__` uses PyPI-compatible format).
- Local plugins skipped during version checks and updates.
- Version display shows tag separately (e.g., `gdpm v0.0.2 [beta]`).
- Hash-based change detection for local plugins (skip unchanged).
- Rename detection for local plugins.

### Bug Fixes

- Fixed compatibility check for plugins with `None` max Godot version.
- Fixed `gdpm lock` to skip local plugins.
- Fixed `gdpm sync` to update lock file for local plugins.
- Fixed Windows build workflow (cache paths, entry point, archive).

### Infrastructure

- AGENTS.md for AI agent context.
- Code quality check script (`scripts/check.py`).
- Version management script (`scripts/version.py`).
