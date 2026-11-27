# Installation

## pip (recommended)

```bash
pip install godot-gdpm
```

## GitHub Releases

Download from [Releases](https://github.com/Abyss-PlayerEG/godot-gdpm/releases).

=== "macOS / Linux"

    ```bash
    tar -xzf gdpm_*_*.tar.gz
    cd gdpm
    ./install.sh
    ```

=== "Windows"

    Extract the zip and run `install.bat`.

!!! note "Unsigned binaries"
    Release binaries are built ad-hoc (no Apple Developer ID / not notarized).
    `install.sh` removes the macOS quarantine attribute automatically.

    On Windows, SmartScreen will warn on first run — choose "More info" → "Run anyway".

## Verify

```bash
gdpm -V
```
