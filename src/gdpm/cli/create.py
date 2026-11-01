"""
gdpm create 命令

- 创建新的 Godot 项目: 询问信息, 生成文件, 可选设置引擎并打开编辑器.

----

Notes
----
- 询问信息: 项目名与 Godot 版本.
- 生成文件: project.godot, gdproject.toml 与 addons/ 目录.
- 后续操作: 可选设置项目引擎并打开 Godot 编辑器.
- create: 命令入口.
- _get_installed_engines: 收集已安装引擎 ID.
- _get_installed_versions: 提取去重版本并过滤 csharp/mono.
- _get_godot_version_tag: 版本转特性标签.
- _set_project_engine: 写入 .engines-conf.json.
- _open_godot: 启动 Godot 编辑器.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import click
import questionary

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.godot.common import get_engines_dir, normalize_version
from gdpm.config.local_engines import get_default_engine, get_local_engine
from gdpm.config.project import ProjectConfig, write_project_config


def _get_installed_engines() -> list[str]:
    """
    获取所有已安装引擎 ID.

    ----

    Returns
    ----
    list[str]
        ID 列表, 如 ['gdpm-godot@4.7-stable', 'steam@4.7-stable'].
    """
    engines: list[str] = []

    # 已下载的引擎 (含 csharp)
    engines_dir = get_engines_dir()
    if engines_dir.exists():
        for d in engines_dir.iterdir():
            if d.is_dir() and d.name[0].isdigit():
                engines.append(f"gdpm-godot@{d.name}")

    # 本地注册的引擎
    from gdpm.config.local_engines import load_local_engines

    for name, engine in load_local_engines().items():
        if engine.version:
            engines.append(f"{name}@{engine.version}")

    # 排序: stable 优先, 再按版本降序
    def sort_key(item: str) -> tuple[int, str]:
        """
        生成排序键.

        stable 版本优先, 其余按版本字符串降序.

        ----

        Parameters
        ----
        item : str
            形如 name@version 的引擎 ID.

        Returns
        ----
        tuple[int, str]
            (是否非 stable, 版本字符串) 二元组.
        """
        ver = item.split("@", 1)[1]
        is_stable = 0 if "stable" in ver else 1
        return (is_stable, ver)

    engines.sort(key=sort_key, reverse=True)
    return engines


def _get_installed_versions(engines: list[str]) -> list[str]:
    """
    从引擎 ID 提取去重版本并过滤 csharp/mono.

    ----

    Parameters
    ----
    engines : list[str]
        引擎 ID 列表.

    Returns
    ----
    list[str]
        去重且不含 csharp/mono 的版本列表.
    """
    versions: list[str] = []
    seen: set[str] = set()

    for engine_id in engines:
        ver = engine_id.split("@", 1)[1]
        if "-csharp" in ver or "-mono" in ver:
            continue
        if ver not in seen:
            seen.add(ver)
            versions.append(ver)

    return versions


def _get_godot_version_tag(version: str) -> str:
    """
    将版本转换为 Godot 特性标签.

    ----

    Parameters
    ----
    version : str
        Godot 版本字符串.

    Returns
    ----
    str
        主次版本号标签, 如 '4.7'.

    Examples
    ----
    >>> _get_godot_version_tag("4.7-stable")
        '4.7'
    >>> _get_godot_version_tag("3.6.2-stable")
        '3.6'
    """
    ver = version.replace("-stable", "").replace("-rc", "").replace("-beta", "")
    parts = ver.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return ver


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm create", "Interactive create"),
        ("gdpm create my-game", "Create with name"),
        ("gdpm create my-game --open", "Create and open Godot"),
    ],
)
@click.argument("name", required=False)
@click.option(
    "--open",
    "-o",
    "open_editor",
    is_flag=True,
    help="Open Godot after create",
)
@click.option("--yes", "-y", is_flag=True, help="Use defaults, skip prompts")
def create(name: str | None, open_editor: bool, yes: bool) -> None:
    """创建新的 Godot 项目."""
    project_dir = Path.cwd()

    console.print("[bold cyan]✦ Create a new Godot project[/bold cyan]")

    # 获取项目名称
    if not name:
        if yes:
            name = "gdpm-project"
        else:
            name = questionary.text(
                "Project name:",
                default="gdpm-project",
            ).ask()
            if not name:
                return

    # 检查目录是否已存在
    target_dir = project_dir / name if name != project_dir.name else project_dir
    config_path = target_dir / "gdproject.toml"

    if config_path.exists():
        console.print(
            f"  [red]✖[/red] Project already exists ([cyan]{config_path}[/cyan])"
        )
        return

    # 获取 Godot 版本
    engines = _get_installed_engines()
    versions = _get_installed_versions(engines)
    default_ver = versions[0] if versions else "4.7-stable"

    if yes:
        godot_ver = default_ver
    elif versions:
        godot_ver = questionary.select(
            "Godot version:",
            choices=versions,
            default=default_ver,
        ).ask()
        if not godot_ver:
            return
    else:
        godot_ver = questionary.text(
            "Godot version:",
            default="4.7-stable",
        ).ask()
        if not godot_ver:
            return

    # 规范化版本号
    for suffix in ("-stable", "-csharp", "-mono"):
        godot_ver = godot_ver.replace(suffix, "")
    version_tag = _get_godot_version_tag(godot_ver)

    # 创建项目目录
    target_dir.mkdir(parents=True, exist_ok=True)

    # 生成 project.godot (Godot 4 与 3 格式不同)
    project_godot = target_dir / "project.godot"

    major = int(version_tag.split(".")[0])
    if major >= 4:
        project_godot.write_text(
            f"""; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=5

[application]

config/name="{name}"
config/features=PackedStringArray("{version_tag}")
""",
            encoding="utf-8",
        )
    else:
        project_godot.write_text(
            f"""; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=4

[application]

config/name="{name}"
config/version="{version_tag}.0"
""",
            encoding="utf-8",
        )

    # 创建 addons/ 目录
    addons_dir = target_dir / "addons"
    addons_dir.mkdir(exist_ok=True)

    # 生成 gdproject.toml
    config = ProjectConfig(
        name=name,
        godot=f">={version_tag}.0",
    )
    write_project_config(config, config_path)

    # 显示创建成功信息
    console.print(
        f"\n  [green]✔[/green] Project [bold]{name}[/bold] created successfully!\n"
        f"  [dim]Godot:[/dim]     [cyan]>={version_tag}.0[/cyan]\n"
        f"  [dim]Directory:[/dim] [cyan]{target_dir}[/cyan]\n"
        f"  [dim]Files created:[/dim]\n"
        f"    [cyan]project.godot[/cyan]\n"
        f"    [cyan]gdproject.toml[/cyan]\n"
        f"    [cyan]addons/[/cyan]"
    )

    # 可选: 为该项目设置引擎
    # 按所选版本过滤引擎
    matching_engines = [e for e in engines if godot_ver in e]

    if matching_engines and not yes:
        set_engine = questionary.confirm(
            "Set Godot engine for this project?",
            default=True,
        ).ask()

        if set_engine:
            engine_id = ""
            if len(matching_engines) == 1:
                engine_id = matching_engines[0]
            else:
                engine_id = questionary.select(
                    "Select engine:",
                    choices=matching_engines,
                    default=matching_engines[0],
                ).ask()

            if engine_id:
                _set_project_engine(target_dir, engine_id)

    # 打开 Godot 编辑器
    if open_editor:
        _open_godot(target_dir, godot_ver)


def _set_project_engine(project_dir: Path, engine_id: str) -> None:
    """
    为项目设置 Godot 引擎.

    ----

    Parameters
    ----
    project_dir : Path
        项目根目录.
    engine_id : str
        引擎 ID, 如 gdpm-godot@4.7-stable.
    """
    import json

    from gdpm.cli.godot.common import get_engines_dir, normalize_version

    name, version = engine_id.split("@", 1)

    # 查找引擎可执行文件
    binary = ""
    if name == "gdpm-godot":
        engines_dir = get_engines_dir()
        tag = normalize_version(version)
        ver_dir = engines_dir / tag
        if ver_dir.exists():
            for app in ver_dir.glob("*.app"):
                b = app / "Contents" / "MacOS" / "Godot"
                if b.exists():
                    binary = str(b)
                    break
            if not binary:
                for f in ver_dir.iterdir():
                    if f.is_file() and not f.suffix:
                        binary = str(f)
                        break
    else:
        from gdpm.config.local_engines import get_local_engine

        engine = get_local_engine(name)
        if engine:
            binary = engine.path

    if not binary:
        console.print("  [dim]Skipping engine setup: engine not found[/dim]")
        return

    # 写入 .engines-conf.json
    conf_path = project_dir / ".engines-conf.json"
    conf = {"godot": {"name": name, "version": version, "path": binary}}
    conf_path.write_text(
        json.dumps(conf, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    console.print(f"  [dim]Engine:[/dim] [cyan]{name}@{version}[/cyan]")


def _open_godot(project_dir: Path, version: str) -> None:
    """
    为项目打开 Godot 编辑器.

    ----

    Parameters
    ----
    project_dir : Path
        项目根目录.
    version : str
        Godot 版本.
    """
    binary = ""

    # 优先使用默认引擎
    default = get_default_engine()
    if default:
        name, ver = default.split("@", 1)
        if name == "gdpm-godot":
            engines_dir = get_engines_dir()
            tag = normalize_version(ver)
            ver_dir = engines_dir / tag
            if ver_dir.exists():
                for app in ver_dir.glob("*.app"):
                    b = app / "Contents" / "MacOS" / "Godot"
                    if b.exists():
                        binary = str(b)
                        break
                if not binary:
                    for f in ver_dir.iterdir():
                        if f.is_file() and not f.suffix:
                            binary = str(f)
                            break
        else:
            engine = get_local_engine(name)
            if engine:
                binary = engine.path

    if not binary:
        console.print("[dim]  Skipping open: no Godot engine configured[/dim]")
        return

    try:
        with subprocess.Popen(
            [binary, "-e", "--path", str(project_dir)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ):
            pass
        console.print("  Opening [cyan]Godot[/cyan]...")
    except Exception as e:
        console.print(f"  [yellow]Warning:[/yellow] Failed to open Godot: {e}")
