"""
平台检测工具

- 识别当前运行平台并映射为通用或 Godot 风格的平台标识.

----

Notes
----
- get_platform: 通用平台标识.
- get_godot_platform: Godot 风格平台名.
"""

from __future__ import annotations

import platform


def get_platform() -> str:
    """
    获取通用平台标识.

    ----

    Returns
    ----
    str
        形如 'linux.x86_64', 'macos.arm64', 'windows.x86_64'.
    """
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
    """
    获取 Godot 发行版使用的平台名称.

    ----

    Returns
    ----
    str
        'Linux', 'macOS' 或 'Windows'.
    """
    system = platform.system().lower()

    platform_map = {
        "linux": "Linux",
        "darwin": "macOS",
        "windows": "Windows",
    }
    return platform_map.get(system, system)
