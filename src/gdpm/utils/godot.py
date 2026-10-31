"""
Godot project.godot 文件解析, 从 project.godot 文件检测 Godot
引擎版本, 支持 Godot 3.x 与 4.x 格式.

----

Note:
    - 版本检测规则 (按 config_version):
    - config_version=5 -> Godot 4.x:
        config/features=PackedStringArray("4.7", "Forward Plus")
    - config_version=4 -> Godot 3.x: config/version="3.5.2"
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class GodotProject:
    """
    解析后的 Godot 项目信息.

    ----

    Attributes:
        name: 项目名称.
        godot_version: Godot 版本, 如 "4.7".
        config_version: project.godot 的 config_version 值.
        renderer: 渲染器名称.
        features: config/features 特性列表.
    """

    name: str = ""
    godot_version: str = ""
    config_version: int = 0
    renderer: str = ""
    features: list[str] | None = None

    @property
    def version_constraint(self) -> str:
        """
        生成 gdproject.toml 的版本约束字符串.

        Returns:
            形如 ">=4.2.0" 的约束; 版本缺失时返回 ">=3.0".
        """
        if not self.godot_version:
            return ">=3.0"

        parts = self.godot_version.split(".")
        if len(parts) >= 2:
            major = int(parts[0])
            minor = int(parts[1])
            return f">={major}.{minor}.0"

        return f">={self.godot_version}"


def parse_project_godot(path: Path) -> GodotProject:
    """
    解析 project.godot 文件并提取项目信息, 支持 Godot 3.x (config_version=4)
    与 4.x (config_version=5).

    ----

    Args:
        path: project.godot 文件路径.

    Returns:
        解析出的项目信息; 文件不存在或格式过旧时返回空对象.
    """
    if not path.exists():
        return GodotProject()

    content = path.read_text(encoding="utf-8")
    project = _parse_content(content)

    if project.config_version > 0 and project.config_version < 4:
        return GodotProject()

    return project


def _parse_content(content: str) -> GodotProject:
    """
    解析 project.godot 的文本内容.

    ----

    Args:
        content: project.godot 文件内容.

    Returns:
        解析出的项目信息.
    """
    project = GodotProject()

    # 解析 config_version
    match = re.search(r"config_version=(\d+)", content)
    if match:
        project.config_version = int(match.group(1))

    # 解析项目名称
    # Godot 4.x/3.x: config/name="..."
    # Godot 2.x/1.x: name="..."
    match = re.search(r'config/name="([^"]+)"', content)
    if not match:
        match = re.search(r'^name="([^"]+)"', content, re.MULTILINE)
    if match:
        project.name = match.group(1)

    # 按 config_version 解析版本
    if project.config_version >= 5:
        # Godot 4.x: 版本与渲染器记录在 config/features 中,
        # 如 config/features=PackedStringArray("4.7", "Forward Plus")
        match = re.search(r"config/features=PackedStringArray\(([^)]+)\)", content)
        if match:
            features_str = match.group(1)
            features = [
                f.strip().strip('"')
                for f in features_str.split(",")
                if f.strip().strip('"')
            ]
            project.features = features

            # 从 features 中提取版本
            for f in features:
                if re.match(r"^\d+\.\d+", f):
                    project.godot_version = f
                    break

            # 提取渲染器
            renderers = {
                "Forward Plus": "Forward Plus",
                "Mobile": "Mobile",
                "GL Compatibility": "GL Compatibility",
                "GLES2": "GLES2",
                "GLES3": "GLES3",
            }
            for f in features:
                if f in renderers:
                    project.renderer = renderers[f]
                    break

    elif project.config_version == 4:
        # Godot 3.x: 版本记录在 config/version 中, 例如 config/version="3.5.2"
        match = re.search(r'config/version="([^"]+)"', content)
        if match:
            project.godot_version = match.group(1)

        # 尝试检测渲染器
        if "GLES2" in content:
            project.renderer = "GLES2"
        elif "GLES3" in content:
            project.renderer = "GLES3"

    return project


def detect_godot_version(project_dir: Path) -> str:
    """
    从 project.godot 检测 Godot 版本.

    ----

    Args:
        project_dir: 项目根目录.

    Returns:
        形如 "4.7" 或 "3.5" 的版本字符串, 未找到时为空字符串.
    """
    project_file = project_dir / "project.godot"
    project = parse_project_godot(project_file)
    return project.godot_version


def detect_version_constraint(project_dir: Path) -> str:
    """
    检测 gdproject.toml 所需的 Godot 版本约束.

    ----

    Args:
        project_dir: 项目根目录.

    Returns:
        形如 ">=4.2.0" 的约束字符串, 未找到时返回 ">=4.0".
    """
    project_file = project_dir / "project.godot"
    project = parse_project_godot(project_file)
    return project.version_constraint


def detect_godot_binary(path: Path) -> Path | None:
    """
    从给定路径检测 Godot 可执行文件, 对 macOS .app 捆绑包返回
    Contents/MacOS/ 下的二进制, 对 Linux/Windows 则在路径本身可执行时
    直接返回.

    ----

    Args:
        path: 疑似 Godot 可执行文件或 .app 的路径.

    Returns:
        Godot 二进制路径, 无效时返回 None.
    """
    if not path.exists():
        return None

    # macOS .app 捆绑包
    if path.suffix == ".app":
        binary = path / "Contents" / "MacOS" / "Godot"
        if binary.exists():
            return binary
        # 尝试同名二进制 (例如 Godot_mono.app -> Godot_mono)
        binary = path / "Contents" / "MacOS" / path.stem
        if binary.exists():
            return binary
        return None

    # Linux/Windows 可执行文件
    if path.is_file():
        return path

    return None


def get_godot_version(binary: Path) -> str:
    """
    获取 Godot 二进制的版本号, 运行 'godot --version' 并解析输出.

    ----

    Args:
        binary: Godot 可执行文件路径.

    Returns:
        形如 '4.7-stable' 的版本字符串, 失败时为空字符串.
    """
    try:
        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return ""

        version_str = result.stdout.strip()
        # 输出示例: "4.7.0.stable.official.h" -> "4.7-stable"
        return _parse_version_string(version_str)
    except Exception:
        return ""


def _parse_version_string(version_str: str) -> str:
    """
    将 Godot 版本字符串解析为简短格式.

    ----

    Note:
        - '4.7.0.stable.official.h' -> '4.7-stable'
        - '3.6.2.stable.official.h' -> '3.6.2-stable'
        - '4.7.0.rc1.official.h' -> '4.7-rc1'

    ----

    Args:
        version_str: 原始版本字符串.

    Returns:
        简短格式的版本字符串.
    """
    parts = version_str.split(".")
    if len(parts) < 3:
        return version_str

    major = parts[0]
    minor = parts[1]

    # 查找稳定性标签 (stable, rc, beta, dev)
    stability = ""
    for part in parts[2:]:
        if part in ("stable", "rc", "beta", "dev"):
            stability = part
            break

    if stability:
        return f"{major}.{minor}-{stability}"
    return f"{major}.{minor}"
