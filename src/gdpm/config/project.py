"""Project configuration (gdproject.toml) reader and writer."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from gdpm.models.dependency import Dependency

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ProjectConfig:
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
        if isinstance(spec, str):
            dependencies[name] = Dependency.from_spec(name, spec)
        elif isinstance(spec, dict):
            dep = Dependency.from_spec(
                name,
                spec.get("version", "*"),
                publisher_slug=spec.get("publisher", ""),
                path=spec.get("path", ""),
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
            if dep.publisher_slug or dep.path:
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
            if dep.publisher_slug or dep.path:
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
