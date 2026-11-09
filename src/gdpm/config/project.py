"""
项目配置文件管理

- 读写项目根目录的 gdproject.toml, 声明项目元信息与插件依赖.

----

Examples
----
配置文件结构:

    [project]
    name = "my-game"
    version = "0.1.0"
    godot = ">=4.0"
    license = "MIT"
    addons_dir = "addons"

    [dependencies]
    limbo-ai = "1.2.0"  # 简写版本约束
    my-plugin = { version = "1.0", publisher = "someone", path = "..." }
    local-plugin = { local = true }

    [dev-dependencies]
    debug-tool = "*"

    [scripts]
    run = "godot --path ."

Notes
----
- ProjectConfig: 项目配置数据类.
- read_project_config: 读取 gdproject.toml.
- write_project_config: 写入 gdproject.toml.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from gdpm.models.dependency import Dependency

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ProjectConfig:
    """
    项目配置

    对应 gdproject.toml 中的 [project] 及各依赖/脚本小节.

    ----

    Attributes
    ----
    name : str
        项目名称.
    version : str
        项目版本.
    description : str
        项目描述.
    godot : str
        Godot 引擎版本约束.
    license : str
        开源许可证.
    addons_dir : str
        插件安装目录名.
    dependencies : dict[str, Dependency]
        运行时插件依赖.
    dev_dependencies : dict[str, Dependency]
        开发期插件依赖.
    scripts : dict[str, str]
        自定义脚本命令.
    registries : dict[str, str]
        自定义注册表地址.
    """

    name: str = ""
    version: str = "0.1.0"
    description: str = ""
    godot: str = ">=4.0"
    license: str = "MIT"
    addons_dir: str = "addons"
    dependencies: dict[str, Dependency] = field(default_factory=dict)
    dev_dependencies: dict[str, Dependency] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)
    registries: dict[str, str] = field(default_factory=dict)


def read_project_config(path: Path) -> ProjectConfig:
    """
    读取项目配置文件.

    解析 gdproject.toml 中的 [project], [dependencies], [dev-dependencies],
    [scripts] 与 [registries] 小节.

    ----

    Parameters
    ----
    path : Path
        gdproject.toml 的路径.

    Returns
    ----
    ProjectConfig
        解析得到的项目配置.

    Raises
    ----
    FileNotFoundError
        配置文件不存在.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")

    with open(path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    project = data.get("project", {})
    deps_raw = data.get("dependencies", {})
    dev_deps_raw = data.get("dev-dependencies", {})
    scripts = data.get("scripts", {})
    registries = data.get("registries", {})

    dependencies: dict[str, Dependency] = {}
    for name, spec in deps_raw.items():
        # 依赖支持简写字符串与完整对象表两种写法
        if isinstance(spec, str):
            dependencies[name] = Dependency.from_spec(name, spec)
        elif isinstance(spec, dict):
            dep = Dependency.from_spec(
                name,
                spec.get("version", "*"),
                publisher_slug=spec.get("publisher", ""),
                path=spec.get("path", ""),
                is_local=spec.get("local", False),
            )
            dependencies[name] = dep

    dev_dependencies: dict[str, Dependency] = {}
    for name, spec in dev_deps_raw.items():
        if isinstance(spec, str):
            dev_dependencies[name] = Dependency.from_spec(name, spec, is_dev=True)
        elif isinstance(spec, dict):
            dev_dependencies[name] = Dependency.from_spec(
                name,
                spec.get("version", "*"),
                publisher_slug=spec.get("publisher", ""),
                path=spec.get("path", ""),
                is_local=spec.get("local", False),
                is_dev=True,
            )

    return ProjectConfig(
        name=project.get("name", ""),
        version=project.get("version", "0.1.0"),
        description=project.get("description", ""),
        godot=project.get("godot", ">=4.0"),
        license=project.get("license", "MIT"),
        addons_dir=project.get("addons_dir", "addons"),
        dependencies=dependencies,
        dev_dependencies=dev_dependencies,
        scripts=dict(scripts),
        registries=dict(registries),
    )


def write_project_config(config: ProjectConfig, path: Path) -> None:
    """
    写入项目配置文件.

    将配置序列化为 TOML 并覆盖写入目标文件.

    依赖的三种写法:
    - 本地插件: ``name = { local = true }``.
    - 含 publisher 或 path:
        ``name = { version = "...", publisher = "...", path = "..." }``.
    - 普通版本约束: ``name = "1.0"``.

    ----

    Parameters
    ----
    config : ProjectConfig
        要写入的项目配置.
    path : Path
        gdproject.toml 的路径.
    """
    lines: list[str] = []

    lines.append("[project]")
    lines.append(f'name = "{config.name}"')
    lines.append(f'version = "{config.version}"')
    if config.description:
        lines.append(f'description = "{config.description}"')
    lines.append(f'godot = "{config.godot}"')
    lines.append(f'license = "{config.license}"')
    lines.append(f'addons_dir = "{config.addons_dir}"')
    lines.append("")

    if config.dependencies:
        lines.append("[dependencies]")
        for name, dep in config.dependencies.items():
            if dep.is_local:
                lines.append(f"{name} = {{ local = true }}")
            elif dep.publisher_slug or dep.path:
                parts = [f'version = "{dep.constraint}"']
                if dep.publisher_slug:
                    parts.append(f'publisher = "{dep.publisher_slug}"')
                if dep.path:
                    parts.append(f'path = "{dep.path}"')
                lines.append(f"{name} = {{ {', '.join(parts)} }}")
            else:
                lines.append(f'{name} = "{dep.constraint}"')
        lines.append("")

    if config.dev_dependencies:
        lines.append("[dev-dependencies]")
        for name, dep in config.dev_dependencies.items():
            if dep.is_local:
                lines.append(f"{name} = {{ local = true }}")
            elif dep.publisher_slug or dep.path:
                parts = [f'version = "{dep.constraint}"']
                if dep.publisher_slug:
                    parts.append(f'publisher = "{dep.publisher_slug}"')
                if dep.path:
                    parts.append(f'path = "{dep.path}"')
                lines.append(f"{name} = {{ {', '.join(parts)} }}")
            else:
                lines.append(f'{name} = "{dep.constraint}"')
        lines.append("")

    if config.scripts:
        lines.append("[scripts]")
        for name, cmd in config.scripts.items():
            lines.append(f'{name} = "{cmd}"')
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
