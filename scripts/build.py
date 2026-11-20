#!/usr/bin/env python3
"""Build script for gdpm.

Usage:
    python scripts/build.py                 # Build for current platform
    python scripts/build.py --tag v0.1.0    # Tag used in archive name
"""

from __future__ import annotations

import argparse
import io
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Windows pipes default to cp1252 — keep ✓/✗ output printable everywhere
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).parent.parent
DIST_DIR = PROJECT_DIR / "dist"
SRC_DIR = PROJECT_DIR / "src"
ICON_DIR = PROJECT_DIR


def get_platform() -> tuple[str, str]:
    """Detect platform and architecture."""
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin":
        return "macos", "arm64" if machine == "arm64" else "x86_64"
    if system == "Windows":
        arch = "amd64" if machine.upper() in ("AMD64", "X86_64") else machine.lower()
        return "windows", arch
    arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(machine, machine)
    return "linux", arch


def get_linux_suffix() -> str:
    """Build distro suffix from /etc/os-release, e.g. ubuntu2204."""
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return ""
    values: dict[str, str] = {}
    for line in os_release.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key] = value.strip().strip('"')
    os_id = values.get("ID", "")
    if not os_id:
        return ""
    version = values.get("VERSION_ID", "").replace(".", "")
    return f"{os_id}{version}" if version else os_id


def get_version() -> str:
    """Get version from pyproject.toml."""
    init_file = SRC_DIR / "gdpm" / "__init__.py"
    content = init_file.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.startswith("__version__"):
            return line.split('"')[1]
    return "0.0.0"


def build(tag: str = "") -> None:
    """Build executable."""
    plat, arch = get_platform()
    version = get_version()
    tag = tag or f"v{version}"

    print(f"  Platform: {plat} {arch}")
    print(f"  Version:  v{version}")
    print()

    # PyInstaller args
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onedir",
        "--name",
        "gdpm",
        "--paths",
        str(SRC_DIR),
        "--noconfirm",
        "--clean",
    ]

    # Icon: PyInstaller only applies it to Windows .exe and macOS .app bundles
    if plat == "windows":
        icon = ICON_DIR / "icon.ico"
        if icon.exists():
            args.extend(["--icon", str(icon)])

    # Entry point
    args.append(str(SRC_DIR / "gdpm" / "__main__.py"))

    print("  Building with PyInstaller...")
    result = subprocess.run(args, cwd=PROJECT_DIR, check=False)

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
        shutil.copy(
            PROJECT_DIR / "installer" / "Windows" / "install-windows-gdpm.bat",
            dist_gdpm,
        )
        shutil.copy(
            PROJECT_DIR / "installer" / "Windows" / "uninstall-windows-gdpm.bat",
            dist_gdpm,
        )

    # Ensure shell scripts are executable in the archive (git may not preserve the bit)
    for script in dist_gdpm.glob("*.sh"):
        script.chmod(0o755)

    # Create archive
    suffix = f"_{plat}_{arch}"
    if plat == "linux":
        distro_suffix = get_linux_suffix()
        if distro_suffix:
            suffix += f"_{distro_suffix}"

    archive_name = f"gdpm_{tag}{suffix}"
    print(f"\n  Creating archive: {archive_name}")

    if plat == "windows":
        shutil.make_archive(str(DIST_DIR / archive_name), "zip", DIST_DIR, "gdpm")
        print(f"  ✓ Created {archive_name}.zip")
    else:
        shutil.make_archive(str(DIST_DIR / archive_name), "gztar", DIST_DIR, "gdpm")
        print(f"  ✓ Created {archive_name}.tar.gz")

    print("\n  Build complete! Output in dist/")
    print("  Verify with: python3 scripts/smoke.py")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build gdpm executable")
    parser.add_argument("--tag", default="", help="Tag used in archive name")

    args = parser.parse_args()

    build(tag=args.tag)


if __name__ == "__main__":
    main()
