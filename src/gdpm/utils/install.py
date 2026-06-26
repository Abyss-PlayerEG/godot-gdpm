"""Install type detection."""

from __future__ import annotations

import platform
import sys


def get_install_type() -> str:
    """Detect how gdpm was installed.

    Returns:
        'binary' - PyInstaller/Nuitka compiled
        'pip'    - pip install
        'source' - development/source install
    """
    if getattr(sys, 'frozen', False):
        return 'binary'
    try:
        from importlib.metadata import version
        version('godot-gdpm')
        return 'pip'
    except Exception:
        return 'source'


def get_platform() -> str:
    """Get user platform info.

    Returns:
        e.g. 'macOS arm64', 'Windows x64', 'Linux x86_64'
    """
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin":
        return f"macOS {machine}"
    if system == "Windows":
        arch = platform.architecture()[0]
        return f"Windows {'x64' if '64' in arch else 'x86'}"
    return f"Linux {machine}"


def get_godot_platform() -> str:
    """Get Godot download platform identifier.

    Returns:
        e.g. 'macos.universal', 'linux.x86_64', 'win64'
    """
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin":
        return "macos.universal"
    if system == "Windows":
        return "win64"
    # Linux
    if machine in ("x86_64", "amd64"):
        return "linux.x86_64"
    if machine in ("aarch64", "arm64"):
        return "linux.arm64"
    return "linux.x86_64"


def get_godot_ext() -> str:
    """Get Godot download file extension.

    Returns:
        e.g. 'zip', 'exe.zip'
    """
    if platform.system() == "Windows":
        return "exe.zip"
    return "zip"
