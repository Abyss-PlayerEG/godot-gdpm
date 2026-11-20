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

=== "macOS"

    ```bash
    gdpm godot add /Applications/Godot.app
    ```

=== "Linux"

    ```bash
    gdpm godot add /usr/local/bin/godot
    ```

=== "Windows"

    ```bash
    gdpm godot add "C:\Program Files\Godot\Godot.exe"
    ```

With alias:

```bash
gdpm godot add /path/to/Godot --name 4.7-custom
```

!!! note
    Use quotes when the path contains spaces. This applies to all platforms.

## List engines

=== "Installed"

    ```bash
    gdpm godot list
    ```

    ```
    ╭──────────────────── Installed Godot (3) ─────────────────────╮
    │                                                              │
    │   Name               Version              Source             │
    │  ────────────────────────────────────────────────────────    │
    │   gdpm-godot         4.4-stable           ~/.gdpm/engines/   │
    │   gdpm-godot         4.4-stable-csharp    ~/.gdpm/engines/   │
    │   steam-godot        4.7-stable           ~/Library/...      │
    │                                                              │
    ╰──────────────────────────────────────────────────────────────╯
    ```

=== "Compact ID"

    ```bash
    gdpm godot list -id
    ```

    ```
    ╭──────────────────── Installed Godot (3) ─────────────────────╮
    │                                                              │
    │   ID                              Source                     │
    │  ────────────────────────────────────────────────────────    │
    │   gdpm-godot@4.4-stable           ~/.gdpm/engines/...        │
    │   gdpm-godot@4.4-stable-csharp    ~/.gdpm/engines/...        │
    │   steam-godot@4.7-stable          ~/Library/...              │
    │                                                              │
    ╰──────────────────────────────────────────────────────────────╯
    ```

=== "Remote"

    ```bash
    gdpm godot list -r
    ```

    ```
    ╭────────────── Available Godot Versions (page 1/3) ───────────╮
    │                                                              │
    │   Version                        Type          Date          │
    │  ────────────────────────────────────────────────────────    │
    │   4.7-stable                     Stable        2026-06-18    │
    │   4.6.3-stable                   Stable        2026-05-20    │
    │   4.6.2-stable                   Stable        2026-04-01    │
    │   4.5.2-stable                   Stable        2026-03-19    │
    │   ...                                                        │
    │                                                              │
    ╰──────────────────────────────────────────────────────────────╯
    ```

    Additional options:

    | Option | Description |
    |--------|-------------|
    | `-V, --version <ver>` | Filter by version (e.g., `4.7`, `3.6`) |
    | `-a, --all` | Show all versions including 1.x/2.x |
    | `-p, --page <num>` | Page number for pagination |

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
