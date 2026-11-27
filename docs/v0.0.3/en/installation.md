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
    sudo mv gdpm /usr/local/bin/
    ```

=== "Windows"

    Extract the zip and add the folder containing `gdpm.exe` to your `PATH`.

!!! note "Unsigned binaries"
    Release binaries are built ad-hoc (no Apple Developer ID / not notarized).
    On macOS, remove the quarantine attribute before running:

    ```bash
    xattr -cr gdpm
    ```

    On Windows, SmartScreen will warn on first run — choose "More info" → "Run anyway".

## Verify

```bash
gdpm -V
```
