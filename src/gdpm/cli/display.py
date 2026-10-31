"""
CLI 展示工具. 提供插件版本兼容性与元数据的格式化/打印函数, 以及 JSON 输出工具.

----

Note:
    - format_version_info / display_version_info: 版本与兼容性信息.
    - format_plugin_meta / display_plugin_meta: 插件元数据.
    - output_json: JSON 输出.
"""

from __future__ import annotations

from gdpm.cli.common import console
from gdpm.utils.version import is_compatible


def format_version_info(
    ver: str,
    min_godot: str,
    max_godot: str,
    project_godot: str = "",
) -> list[str]:
    """
    格式化版本与兼容性信息行.

    ----

    Args:
        ver: 插件版本号.
        min_godot: 最低 Godot 版本, 可为空.
        max_godot: 最高 Godot 版本, 可为空.
        project_godot: 项目 Godot 版本, 为空则不做兼容性判断.

    Returns:
        可直接传给 console.print 的富文本行列表.
    """
    lines = []
    # 统一显示为 v 前缀
    ver_display = ver if ver.startswith(("v", "V")) else f"v{ver}"
    lines.append(f"    [dim]{ver_display}[/dim]")

    # 字符串 "None" 与空串同样视为未设置
    godot_parts = []
    if min_godot and min_godot not in ("None", ""):
        godot_parts.append(f">={min_godot}")
    if max_godot and max_godot not in ("None", ""):
        godot_parts.append(f"<={max_godot}")

    if godot_parts:
        lines.append(f"    [dim]Godot {' '.join(godot_parts)}[/dim]")

    # 提供项目 Godot 版本时输出兼容性标记
    if project_godot:
        compatible, msg = is_compatible(project_godot, min_godot, max_godot)
        if compatible:
            lines.append("    [green]✓ Compatible[/green]")
        else:
            lines.append(f"    [red]✗ {msg}[/red]")

    return lines


def format_plugin_meta(
    license_name: str = "",
    stars: int = 0,
    tags: list[str] | None = None,
    store_url: str = "",
) -> list[str]:
    """
    格式化插件元数据行.

    ----

    Args:
        license_name: 许可证名称.
        stars: 商店评分或星数.
        tags: 标签列表.
        store_url: 商店页面地址.

    Returns:
        可直接传给 console.print 的富文本行列表.
    """
    lines = []
    parts = []
    if license_name:
        parts.append(f"License: {license_name}")
    if stars:
        parts.append(f"Score: {stars}")
    meta = "  |  ".join(parts)
    if meta:
        lines.append(f"    [dim]{meta}[/dim]")
    if tags:
        lines.append(f"    [dim]Tags: {', '.join(tags)}[/dim]")
    if store_url:
        lines.append(f"    [dim]{store_url}[/dim]")
    return lines


def display_version_info(
    ver: str,
    min_godot: str,
    max_godot: str,
    project_godot: str = "",
) -> None:
    """
    打印版本与兼容性信息.

    ----

    Args:
        ver: 插件版本号.
        min_godot: 最低 Godot 版本.
        max_godot: 最高 Godot 版本.
        project_godot: 项目 Godot 版本.
    """
    lines = format_version_info(ver, min_godot, max_godot, project_godot)
    console.print("\n".join(lines))


def display_plugin_meta(
    license_name: str = "",
    stars: int = 0,
    tags: list[str] | None = None,
    store_url: str = "",
) -> None:
    """
    打印插件元数据.

    ----

    Args:
        license_name: 许可证名称.
        stars: 商店评分或星数.
        tags: 标签列表.
        store_url: 商店页面地址.
    """
    lines = format_plugin_meta(license_name, stars, tags, store_url)
    console.print("\n".join(lines))


def output_json(data: object) -> None:
    """
    以 JSON 格式打印数据.

    ----

    Args:
        data: 可被 json 序列化的数据.
    """
    import json

    console.print(json.dumps(data, indent=2, ensure_ascii=False))
