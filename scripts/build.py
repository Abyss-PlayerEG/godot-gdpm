#!/usr/bin/env python3
"""Build script for gdpm.

Usage:
    python scripts/build.py              # Build for current platform
    python scripts/build.py --clean      # Clean build artifacts
    python scripts/build.py --version    # Show version
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
SRC_DIR = PROJECT_DIR / "src"
ICON_DIR = PROJECT_DIR


def get_platform() -> tuple[str, str]:
    """Detect platform and architecture."""
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin":
        return "macos", "arm64" if machine == "arm64" else "x86_64"
    if system == "Windows":
        arch = platform.architecture()[0]
        return "windows", "amd64" if "64" in arch else "x86"
    return "linux", machine


def get_version() -> str:
    """Get version from pyproject.toml."""
    init_file = SRC_DIR / "gdpm" / "__init__.py"
    content = init_file.read_text()
    for line in content.splitlines():
        if line.startswith("__version__"):
            return line.split('"')[1]
    return "0.0.0"


def clean() -> None:
    """Clean build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed {d.name}/")

    for spec in PROJECT_DIR.glob("*.spec"):
        spec.unlink()
        print(f"  Removed {spec.name}")


def build() -> None:
    """Build executable."""
    plat, arch = get_platform()
    version = get_version()

    print(f"  Platform: {plat} {arch}")
    print(f"  Version:  v{version}")
    print()

    # PyInstaller args
    args = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", "gdpm",
        "--paths", str(SRC_DIR),
        "--noconfirm",
        "--clean",
    ]

    # Add icon
    if plat == "windows":
        icon = ICON_DIR / "icon.ico"
    else:
        icon = ICON_DIR / "icon.png"

    if icon.exists():
        args.extend(["--icon", str(icon)])

    # Entry point
    args.append(str(SRC_DIR / "gdpm" / "__main__.py"))

    print("  Building with PyInstaller...")
    result = subprocess.run(args, cwd=PROJECT_DIR)

    if result.returncode != 0:
        print("  ✗ Build failed!")
        sys.exit(1)

    # Copy installer scripts
    dist_gdpm = DIST_DIR / "gdpm"
    if plat == "linux":
        shutil.copy(PROJECT_DIR / "installer" / "Linux" / "install.sh", dist_gdpm)
        shutil.copy(PROJECT_DIR / "installer" / "Linux" / "uninstall.sh", dist_gdpm)
    elif plat == "macos":
        shutil.copy(PROJECT_DIR / "installer" / "macOS" / "install.sh", dist_gdpm)
        shutil.copy(PROJECT_DIR / "installer" / "macOS" / "uninstall.sh", dist_gdpm)
    elif plat == "windows":
        shutil.copy(PROJECT_DIR / "installer" / "Windows" / "install.bat", dist_gdpm)
        shutil.copy(PROJECT_DIR / "installer" / "Windows" / "uninstall.bat", dist_gdpm)

    # Create archive
    suffix = f"_{plat}_{arch}"
    if plat == "linux":
        # Detect distro
        try:
            import distro
            suffix += f"_{distro.id()}{distro.version()}"
        except ImportError:
            pass

    archive_name = f"gdpm_v{version}{suffix}"
    print(f"\n  Creating archive: {archive_name}")

    if plat == "windows":
        shutil.make_archive(str(DIST_DIR / archive_name), "zip", DIST_DIR, "gdpm")
        print(f"  ✓ Created {archive_name}.zip")
    else:
        shutil.make_archive(str(DIST_DIR / archive_name), "gztar", DIST_DIR, "gdpm")
        print(f"  ✓ Created {archive_name}.tar.gz")

    print(f"\n  Build complete! Output in dist/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build gdpm executable")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--version", action="store_true", help="Show version")

    args = parser.parse_args()

    if args.version:
        print(f"gdpm v{get_version()}")
        return

    if args.clean:
        clean()
        return

    build()


if __name__ == "__main__":
    main()
