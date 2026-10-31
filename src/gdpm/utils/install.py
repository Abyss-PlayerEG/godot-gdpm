"""
安装类型检测, 识别 gdpm 的安装方式, 并提供平台与 Godot 下载标识的查询.

Install type detection. Detect how gdpm was installed and query platform
and Godot download identifiers.

----

Note:
    - get_install_type: 安装方式检测 / Install type detection.
    - get_platform: 用户平台信息 / User platform info.
    - get_godot_platform / get_godot_ext: Godot 下载标识与扩展名 /
        Godot download identifier and file extension.
"""

from __future__ import annotations

import platform
import sys


def get_install_type() -> str:
    """
    检测 gdpm 的安装方式.

    Detect how gdpm was installed.

    ----

    Note:
        - 'binary': PyInstaller/Nuitka 编译版 / compiled binary.
        - 'pip': pip 安装 / pip install.
        - 'source': 开发或源码安装 / development or source install.

    Returns:
        安装方式标识, 'binary', 'pip' 或 'source' / Install type
            identifier: 'binary', 'pip' or 'source'.
    """
    if getattr(sys, "frozen", False):
        return "binary"
    try:
        from importlib.metadata import version

        version("godot-gdpm")
        return "pip"
    except Exception:
        return "source"


def get_platform() -> str:
    """
    获取用户平台信息.

    Get user platform info.

    Returns:
        例如 'macOS arm64', 'Windows x64', 'Linux x86_64' /
            e.g. 'macOS arm64', 'Windows x64', 'Linux x86_64'.
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
    """
    获取 Godot 下载用的平台标识.

    Get Godot download platform identifier.

    Returns:
        例如 'macos.universal', 'linux.x86_64', 'win64' /
            e.g. 'macos.universal', 'linux.x86_64', 'win64'.
    """
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin":
        return "macos.universal"
    if system == "Windows":
        return "win64"
    # Linux 平台 / Linux platform
    if machine in ("x86_64", "amd64"):
        return "linux.x86_64"
    if machine in ("aarch64", "arm64"):
        return "linux.arm64"
    return "linux.x86_64"


def get_godot_ext() -> str:
    """
    获取 Godot 下载文件的扩展名.

    Get Godot download file extension.

    Returns:
        例如 'zip', 'exe.zip' / e.g. 'zip', 'exe.zip'.
    """
    if platform.system() == "Windows":
        return "exe.zip"
    return "zip"
