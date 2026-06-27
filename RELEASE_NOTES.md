# Release Notes

## v0.1.0b1

### New Features

- **Godot Engine Management** — Install, uninstall, and switch Godot engine versions directly from CLI.
  - `gdpm godot install <version>` — Download and install from GitHub (supports `--csharp`).
  - `gdpm godot uninstall <version>` — Remove installed engine.
  - `gdpm godot list` / `gdpm godot list -r` — List installed or remote versions with pagination.
  - `gdpm godot add <path>` — Add a local Godot engine (e.g., Steam version).
  - `gdpm godot remove <name>` — Remove a local engine.
  - `gdpm godot use <id>` — Set engine for current project (`Name@Version` format).
  - `gdpm godot default <id>` — Set fallback engine for projects without explicit config.
  - `gdpm godot info` — Show current engine configuration.
  - `gdpm godot open` — Open Godot editor (`--run` to run project instead).
- **`gdpm create`** — Interactive project creation with engine selection, template detection, and Godot version compatibility.
- **Global Cache** — Shared cache across projects with split index, `gdpm cache info` / `gdpm cache clean`.
- **Export/Import** — `gdpm export` / `gdpm import` with zip archive support.
- **GitHub Token Support** — Auto-detect token from `~/.gdpm/conf.json` for higher API rate limits.
- **`gdpm info` Redesign** — Rich panel with plugin name, version, description, and install details.
- **Download Progress Bar** — Progress bar in `gdpm sync` for parallel downloads (max 5 concurrent).
- **`gdpm sync --frozen`** — Lock file sync for CI environments.
- **Shell Completion** — Tab completion for zsh, bash, fish in install/uninstall scripts.
- **Build Script** — PyInstaller-based build with `scripts/build.py`.
- **`-i` Info Panel** — Version, platform, and install type in `gdpm -i`.
- **`-V` Colored Output** — Version display with platform info, styled like uv.

### Improvements

- Subcommand help redesigned with Rich panels and usage examples.
- `gdpm list` uses Rich panel with color-coded source prefixes.
- `gdpm search` output formatted with panels.
- `gdpm godot add` detects binary, shows version, checks duplicates.
- `gdpm godot list -id` shows compact engine ID view.
- macOS install scripts auto-remove quarantine attributes.
- Hash verification for engine downloads.
- Version normalization (`4.7` → `4.7-stable`).
- Platform-aware download URL resolution via GitHub API.
- `GdpmConsole` auto-adds spacing to all CLI output.
- Suppress SSL verification for GitHub API requests.

### Bug Fixes

- Fixed `gdpm godot open` blocking terminal until Godot exits.
- Fixed `gdpm sync` parallel download passing zip_path correctly.
- Fixed `gdpm create` engine version filtering and deduplication.
- Fixed `gdpm init` preventing overwrite of existing config.
- Fixed `gdpm list` sorting and folder name display.
- Fixed `gdpm info` working outside gdpm projects.
- Fixed deprecated `rmtree` onerror and `Popen` context manager.
- Fixed legacy `except` syntax for PyCharm compatibility.
- Fixed mypy, pylint, and deptry errors.
- Fixed `-h` output with consistent blank line handling.
- Fixed cache index path and download destination directory.
- Fixed `gdpm add --local` scan message formatting.

### Infrastructure

- Pylint added to CI workflow.
- Multi-platform Nuitka build support.
- `scripts/check.py` with legacy syntax check.
- VS Code workspace file.
- AGENTS.md for AI agent context.

## v0.0.6

### Changes

- **Optimized Build** — Changed from `--onefile` to `--onedir` for faster startup (~1s vs ~10s).
- **Platform Archives** — Each platform archive includes install/uninstall scripts.

### Installation

```bash
# macOS / Linux
tar -xzf gdpm_v0.0.6_*.tar.gz
cd gdpm
./install.sh

# Windows
# Extract zip, run install.bat
```

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
