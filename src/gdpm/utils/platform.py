"""Platform detection utilities."""

from __future__ import annotations

import platform


def get_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        return f"linux.{machine}"
    elif system == "darwin":
        if machine == "arm64":
            return "macos.arm64"
        return "macos.x86_64"
    elif system == "windows":
        return "windows.x86_64"

    return f"{system}.{machine}"


def get_godot_platform() -> str:
    system = platform.system().lower()

    platform_map = {
        "linux": "Linux",
        "darwin": "macOS",
        "windows": "Windows",
    }
    return platform_map.get(system, system)
