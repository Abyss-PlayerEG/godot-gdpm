"""
gdpm godot 命令共享工具

- 引擎查找与版本规范化共享工具.

----

Notes
----
- get_engines_dir: 获取全局引擎目录.
- normalize_version: 版本号规范化为 tag 格式.
- build_download_url: 构造官方下载接口 URL (无网络请求).
- fetch_remote_versions: 从官方 versions.json 拉取版本.
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from gdpm.constants import VERSIONS_JSON_URL


def get_engines_dir() -> Path:
    """
    获取全局引擎目录.

    ----

    Returns
    ----
    pathlib.Path
        全局引擎目录路径, 不存在时自动创建.
    """
    engines_dir = Path.home() / ".gdpm" / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    return engines_dir


def normalize_version(version: str) -> str:
    """
    将版本字符串规范化为 tag 格式.

    - '4.7' -> '4.7-stable'
    - '4.7-stable' -> '4.7-stable'
    - '3.6.2' -> '3.6.2-stable'
    - '4.7-stable-csharp' -> '4.7-stable'

    ----

    Parameters
    ----
    version : str
        版本字符串, 可带 -csharp 或 -mono 后缀.

    Returns
    ----
    str
        规范化后的 tag 字符串, 如 '4.7-stable'.

    Examples
    ----
    >>> normalize_version("4.7")
        '4.7-stable'
    """
    version = version.replace("-csharp", "").replace("-mono", "")

    if "-stable" in version or "-rc" in version or "-beta" in version:
        return version
    return f"{version}-stable"


# pylint: disable-next=too-many-return-statements
def _official_asset(version: str, csharp: bool = False) -> tuple[str, str]:
    """
    按平台与版本代际返回官方下载资产的 (slug, platform).

    mono 命名不规则 (linux 变下划线, macOS 保留点), 故用显式代际规则.

    ----

    Parameters
    ----
    version : str
        纯版本号 (不含通道), 如 '4.7.2'.
    csharp : bool, optional
        是否为 C# (mono) 版本.

    Returns
    ----
    tuple[str, str]
        (slug, platform) 二元组, 用于拼接官方下载接口 URL.
    """
    parts = version.split(".")
    try:
        major = int(parts[0])
    except ValueError:
        major = 4
    try:
        minor = int(parts[1])
    except IndexError, ValueError:
        minor = 0

    system = platform.system()
    machine = platform.machine()

    if system == "Windows":
        # mono 无 .exe 后缀 (win64.exe.zip -> mono_win64.zip)
        slug = "mono_win64.zip" if csharp else "win64.exe.zip"
        return slug, "windows.64"

    if system == "Darwin":
        if major < 4:
            slug = "mono_osx.universal.zip" if csharp else "osx.universal.zip"
            return slug, "macos.universal"
        # 4.8 起拆分架构, 之前为 universal
        if (major, minor) >= (4, 8):
            arch = "arm64" if machine == "arm64" else "x86_64"
            slug = f"macos.{arch}.zip"
            return (f"mono_{slug}" if csharp else slug), f"macos.{arch}"
        slug = "mono_macos.universal.zip" if csharp else "macos.universal.zip"
        return slug, "macos.universal"

    # Linux
    if machine in ("aarch64", "arm64"):
        slug = "linux.arm64.zip"
        return (f"mono_{slug}" if csharp else slug), "linux.arm64"
    if major < 4:
        # 3.x 资产名是 x11.64, mono 版为下划线 x11_64
        slug = "mono_x11_64.zip" if csharp else "x11.64.zip"
        return slug, "linux.64"
    slug = "mono_linux_x86_64.zip" if csharp else "linux.x86_64.zip"
    return slug, "linux.64"


def build_download_url(tag: str, csharp: bool = False) -> str:
    """
    构造官方下载接口 URL (downloads.godotengine.org).

    纯字符串拼接无网络请求, 302 重定向由下载时的 httpx 跟随.

    ----

    Parameters
    ----
    tag : str
        发布 tag, 如 '4.7.2-stable'.
    csharp : bool, optional
        是否为 C# (mono) 版本.

    Returns
    ----
    str
        官方下载接口 URL.
    """
    version, _, flavor = tag.partition("-")
    flavor = flavor or "stable"
    slug, platform_id = _official_asset(version, csharp)
    return (
        "https://downloads.godotengine.org/"
        f"?version={version}&flavor={flavor}&slug={slug}&platform={platform_id}"
    )


@dataclass(frozen=True)
class RemoteRelease:
    """
    官方 versions.json 中的单个版本条目.

    ----

    Attributes
    ----
    tag : str
        完整版本标签, 如 '4.8-beta2'.
    date : str
        发布日期 (ISO 格式), 如 '2026-10-29'.
    stable : bool
        是否为 stable 通道.
    channel : str
        发布通道 (去除序号), 如 'beta', 'stable', 'rc', 'dev', 'alpha'.
    """

    tag: str
    date: str
    stable: bool
    channel: str


# versions.json 的日期是英文展示串, 月份名映射用于转 ISO 格式
_DISPLAY_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def _parse_display_date(raw: str) -> str:
    """
    将 versions.json 的展示日期转为 ISO 格式.

    '29 October 2026' -> '2026-10-29', 无法解析时原样返回.

    ----

    Parameters
    ----
    raw : str
        英文展示日期串.

    Returns
    ----
    str
        ISO 日期或原始字符串.
    """
    parts = raw.split()
    if len(parts) != 3 or parts[1] not in _DISPLAY_MONTHS:
        return raw
    month = _DISPLAY_MONTHS[parts[1]]
    return f"{parts[2]}-{month:02d}-{int(parts[0]):02d}"


def _flavor_channel(flavor: str) -> str:
    """
    由版本通道名推导发布通道 (去除尾部序号).

    'beta2' -> 'beta', 'rc10' -> 'rc', 'stable' -> 'stable'.

    ----

    Parameters
    ----
    flavor : str
        versions.json 中的通道名, 可带序号.

    Returns
    ----
    str
        去除序号后的通道名, 无数字时原样返回.
    """
    return flavor.rstrip("0123456789") or flavor


def parse_versions_json(data: list[Any]) -> list[RemoteRelease]:
    """
    将 versions.json 数据展平为版本条目列表.

    按文件原有顺序返回 (新版本在前), tag 由组名与通道名拼接.

    ----

    Parameters
    ----
    data : list
        versions.json 的根数组, 形如 [{name, releases: [...]}].

    Returns
    ----
    list[RemoteRelease]
        展平后的版本条目列表.
    """
    result: list[RemoteRelease] = []
    for group in data:
        version = str(group.get("name", ""))
        for rel in group.get("releases", []):
            flavor = str(rel.get("name", ""))
            if not version or not flavor:
                continue
            result.append(
                RemoteRelease(
                    tag=f"{version}-{flavor}",
                    date=_parse_display_date(str(rel.get("release_date", ""))),
                    stable=flavor == "stable",
                    channel=_flavor_channel(flavor),
                )
            )
    return result


def fetch_remote_versions() -> list[RemoteRelease]:
    """
    从官方 versions.json 拉取全部可用版本.

    静态文件无速率限制, 失败时抛出 httpx 异常由调用方处理.

    ----

    Returns
    ----
    list[RemoteRelease]
        全部版本条目 (新版本在前).

    Raises
    ----
    httpx.HTTPError
        网络请求失败或响应非 2xx.
    """
    resp = httpx.get(VERSIONS_JSON_URL, timeout=10)
    resp.raise_for_status()
    return parse_versions_json(resp.json())


def ensure_executable(path: Path) -> None:
    """
    确保文件具有执行权限 (Windows 上无操作).

    ----

    Parameters
    ----
    path : Path
        需要设置执行权限的文件路径.

    Returns
    ----
    None
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

    - macOS: .app 包 -> Contents/MacOS/Godot, 回退到无后缀二进制.
    - Windows: .exe (优先非 console 版), 兼容 mono 子目录布局.
    - Linux: Godot* 开头的可执行文件 (名字以 .x86_64/.arm64 结尾), 恢复执行位.

    ----

    Parameters
    ----
    directory : Path
        引擎解压目录.

    Returns
    ----
    str | None
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
        # macOS: 优先查找 .app 包内的二进制 (兼容 mono 变体 Godot_mono.app)
        for d in search_dirs:
            for app in sorted(d.glob("*.app")):
                for stem in ("Godot", app.stem):
                    binary = app / "Contents" / "MacOS" / stem
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

    Parameters
    ----
    directory : Path
        解压后的引擎目录.

    Returns
    ----
    None
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

    Parameters
    ----
    name : str
        引擎名称, 'gdpm-godot' 或本地引擎别名.
    version : str
        版本字符串, 本地引擎可为空.

    Returns
    ----
    str | None
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

    比 find_engine 更宽松: 本地引擎仅按名称匹配.

    ----

    Parameters
    ----
    name : str
        引擎名称, 'gdpm-godot' 或本地引擎别名.
    version : str
        版本字符串, 本地引擎可忽略.

    Returns
    ----
    str
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
