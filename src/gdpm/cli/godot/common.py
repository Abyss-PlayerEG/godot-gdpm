"""
gdpm godot 命令共享工具.

----

Note:
    - get_engines_dir: 获取全局引擎目录.
    - normalize_version: 版本号规范化为 tag 格式.
    - build_download_url: 从 GitHub API 获取下载地址.
    - get_asset_hash: 获取发布资源的 SHA256 哈希.
    - ensure_executable: 确保文件具有执行权限.
    - find_engine_binary: 在引擎目录中查找二进制.
    - prepare_engine_dir: 解压后修复权限.
    - find_engine: 按名称和版本查找引擎.
    - resolve_engine_path: 解析 Godot 二进制路径.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

import httpx

from gdpm.constants import GITHUB_API_URL, GODOT_RELEASES_URL, get_github_headers
from gdpm.utils.install import get_godot_platform


def get_engines_dir() -> Path:
    """
    获取全局引擎目录.

    Returns:
        全局引擎目录路径, 不存在时自动创建.
    """
    engines_dir = Path.home() / ".gdpm" / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    return engines_dir


def normalize_version(version: str) -> str:
    """
    将版本字符串规范化为 tag 格式.

    ----

    Note:
        - '4.7' -> '4.7-stable'
        - '4.7-stable' -> '4.7-stable'
        - '3.6.2' -> '3.6.2-stable'
        - '4.7-stable-csharp' -> '4.7-stable'

    ----

    Args:
        version: 版本字符串, 可带 -csharp 或 -mono 后缀.

    Returns:
        规范化后的 tag 字符串, 如 '4.7-stable'.
    """
    version = version.replace("-csharp", "").replace("-mono", "")

    if "-stable" in version or "-rc" in version or "-beta" in version:
        return version
    return f"{version}-stable"


def build_download_url(tag: str, csharp: bool = False) -> str:
    """
    从 GitHub API 获取 Godot 下载地址.

    ----

    Args:
        tag: 发布 tag, 如 '4.7-stable'.
        csharp: 是否获取 C# (mono) 版本.

    Returns:
        下载 URL 字符串, 未匹配到资源或请求失败时返回空字符串.
    """
    mono = "_mono" if csharp else ""
    system = get_godot_platform()

    if "macos" in system:
        keywords: tuple[str, ...] = ("osx", "macos")
    elif "linux" in system:
        keywords = ("linux",)
    else:
        keywords = ("win",)

    try:
        resp = httpx.get(
            f"{GODOT_RELEASES_URL}/tags/{tag}",
            headers=get_github_headers(),
            timeout=10,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()

        for asset in data.get("assets", []):
            name = asset["name"]
            if mono and "_mono" not in name:
                continue
            if not mono and "_mono" in name:
                continue
            if name.endswith(".zip") and any(k in name for k in keywords):
                return str(asset["browser_download_url"])
    except Exception:
        pass

    return ""


def get_asset_hash(tag: str, filename: str) -> str:
    """
    从 GitHub API 获取发布资源的 SHA256 哈希.

    ----

    Args:
        tag: 发布 tag, 如 '4.7-stable'.
        filename: 资源文件名.

    Returns:
        十六进制 SHA256 哈希字符串, 获取失败时返回空字符串.
    """
    try:
        resp = httpx.get(
            f"{GITHUB_API_URL}contributors",
            headers=get_github_headers(),
            timeout=5,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()

        for asset in data.get("assets", []):
            if asset.get("name") == filename:
                digest = asset.get("digest", "")
                if digest.startswith("sha256:"):
                    return str(digest[7:])
        return ""
    except Exception:
        return ""


def ensure_executable(path: Path) -> None:
    """
    确保文件具有执行权限 (Windows 上无操作).

    ----

    Args:
        path: 需要设置执行权限的文件路径.

    Returns:
        无.
    """
    if platform.system() == "Windows":
        # Windows 无执行位概念, 直接返回
        return
    try:
        if not os.access(path, os.X_OK):
            # 追加执行位 (属主/属组/其他)
            path.chmod(path.stat().st_mode | 0o111)
    except OSError:
        # 权限修改失败时静默忽略
        pass


# pylint: disable-next=too-many-return-statements
def find_engine_binary(directory: Path) -> str | None:
    """
    在引擎目录中查找可启动的 Godot 二进制文件 (跨平台).

    ----

    Note:
        - macOS: .app 包 -> Contents/MacOS/Godot, 回退到无后缀二进制.
        - Windows: .exe (优先非 console 版), 兼容 mono 子目录布局.
        - Linux: Godot* 开头的可执行文件 (名字以 .x86_64/.arm64 结尾), 恢复执行位.

    ----

    Args:
        directory: 引擎解压目录.

    Returns:
        Godot 二进制文件路径, 未找到时返回 None.
    """
    system = platform.system()

    # 搜索范围: 根目录 + 子目录 (排除 GodotSharp)
    search_dirs = [directory]
    try:
        search_dirs.extend(
            child
            for child in directory.iterdir()
            if child.is_dir() and child.name != "GodotSharp"
        )
    except OSError:
        return None

    if system == "Darwin":
        # macOS: 优先查找 .app 包内的二进制
        for d in search_dirs:
            for app in sorted(d.glob("*.app")):
                binary = app / "Contents" / "MacOS" / "Godot"
                if binary.exists():
                    return str(binary)

    if system == "Windows":
        # Windows: 收集所有 .exe, 优先非 console 版
        exes: list[Path] = []
        for d in search_dirs:
            try:
                exes.extend(
                    f for f in d.iterdir() if f.is_file() and f.suffix.lower() == ".exe"
                )
            except OSError:
                continue
        for f in exes:
            if "console" not in f.name.lower():
                return str(f)
        if exes:
            return str(exes[0])
        return None

    # Linux/通用: 匹配 Godot* 可执行文件并恢复执行位
    for d in search_dirs:
        try:
            for f in sorted(d.iterdir()):
                if (
                    f.is_file()
                    and f.name.startswith("Godot")
                    and not f.name.endswith(".zip")
                ):
                    ensure_executable(f)
                    return str(f)
        except OSError:
            continue

    if system == "Darwin":
        # macOS 回退: 查找无后缀的二进制文件
        for d in search_dirs:
            try:
                for f in sorted(d.iterdir()):
                    if f.is_file() and not f.suffix:
                        ensure_executable(f)
                        return str(f)
            except OSError:
                continue

    return None


def prepare_engine_dir(directory: Path) -> None:
    """
    解压 Godot 发布包后修复权限 (按平台处理).

    ----

    Args:
        directory: 解压后的引擎目录.

    Returns:
        无.
    """
    if platform.system() == "Darwin":
        # macOS: 清除隔离属性并恢复可执行位
        for app in directory.glob("*.app"):
            # xattr -cr 去除下载隔离属性
            subprocess.run(
                ["xattr", "-cr", str(app)],
                check=False,
                capture_output=True,
            )
            macos_dir = app / "Contents" / "MacOS"
            if macos_dir.exists():
                for binary in macos_dir.iterdir():
                    ensure_executable(binary)

    if platform.system() != "Windows":
        # 非 Windows: 为 Godot 可执行文件恢复执行位
        for f in directory.rglob("*"):
            if (
                f.is_file()
                and f.name.startswith("Godot")
                and "GodotSharp" not in f.parts
            ):
                ensure_executable(f)


def find_engine(name: str, version: str) -> str | None:
    """
    按名称和版本查找 Godot 二进制路径.

    ----

    Args:
        name: 引擎名称, 'gdpm-godot' 或本地引擎别名.
        version: 版本字符串, 本地引擎可为空.

    Returns:
        Godot 二进制路径字符串, 未找到时返回 None.
    """
    from gdpm.config.local_engines import load_local_engines

    engines_dir = get_engines_dir()

    local_engines = load_local_engines()
    if name in local_engines:
        engine = local_engines[name]
        if not version or engine.version == version:
            return engine.path

    if name == "gdpm-godot":
        tag = normalize_version(version) if version else ""
        if tag:
            for candidate in (engines_dir / tag, engines_dir / f"{tag}-csharp"):
                if candidate.exists():
                    binary = find_engine_binary(candidate)
                    if binary:
                        return binary

    return None


def resolve_engine_path(name: str, version: str) -> str:
    """
    按引擎名称和版本解析 Godot 二进制路径.

    ----

    Note:
        - 比 find_engine 更宽松: 本地引擎仅按名称匹配.

    ----

    Args:
        name: 引擎名称, 'gdpm-godot' 或本地引擎别名.
        version: 版本字符串, 本地引擎可忽略.

    Returns:
        Godot 二进制路径字符串, 未找到时返回空字符串.
    """
    from gdpm.config.local_engines import get_local_engine

    if name == "gdpm-godot":
        # 托管引擎: 在全局目录按 tag 查找
        engines_dir = get_engines_dir()
        tag = normalize_version(version) if version else ""
        if tag:
            for candidate in (engines_dir / tag, engines_dir / f"{tag}-csharp"):
                if candidate.exists():
                    binary = find_engine_binary(candidate)
                    if binary:
                        return binary
        return ""

    # 本地引擎: 仅按名称匹配
    engine = get_local_engine(name)
    return engine.path if engine else ""
