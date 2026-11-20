# Installation

## pip (recommended)

```bash
pip install godot-gdpm
```

Pre-release versions require specifying the version:

```bash
pip install godot-gdpm==0.1.0b12
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

    Extract the zip and run `install-windows-gdpm.bat`.

!!! note "Unsigned binaries"
    Release binaries use ad-hoc code signing (no Apple Developer ID / not notarized).
    `install.sh` removes the macOS quarantine attribute automatically. If you run the
    binary directly instead of using the installer:

    ```bash
    xattr -cr gdpm
    ```

    On Windows, SmartScreen will warn on first run — choose "More info" → "Run anyway".

## Verify

```bash
gdpm -V
```
