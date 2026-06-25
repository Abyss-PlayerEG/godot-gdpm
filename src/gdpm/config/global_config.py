"""Global configuration management."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import platformdirs


@dataclass
class GlobalConfig:
    godot_path: str = "godot"
    addons_dir: str = "addons"
    parallel_downloads: int = 4
    cache_dir: str = ""
    store_url: str = "https://store.godotengine.org/api/v1"

    def __post_init__(self) -> None:
        if not self.cache_dir:
            env_dir = os.environ.get("GDPM_CACHE_DIR")
            if env_dir:
                self.cache_dir = env_dir
            else:
                self.cache_dir = str(Path.home() / ".gdpm" / "cache")


def get_config_path() -> Path:
    return Path(platformdirs.user_config_dir("gdpm")) / "config.toml"


def read_global_config() -> GlobalConfig:
    path = get_config_path()
    if not path.exists():
        return GlobalConfig()

    with open(path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    defaults = data.get("defaults", {})
    store = data.get("store", {})
    cache = data.get("cache", {})

    return GlobalConfig(
        godot_path=defaults.get("godot_path", "godot"),
        addons_dir=defaults.get("addons_dir", "addons"),
        parallel_downloads=defaults.get("parallel_downloads", 4),
        cache_dir=cache.get("dir", ""),
        store_url=store.get("base_url", "https://store.godotengine.org/api/v1"),
    )


def write_global_config(config: GlobalConfig) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("[defaults]")
    lines.append(f'godot_path = "{config.godot_path}"')
    lines.append(f'addons_dir = "{config.addons_dir}"')
    lines.append(f"parallel_downloads = {config.parallel_downloads}")
    lines.append("")
    lines.append("[store]")
    lines.append(f'base_url = "{config.store_url}"')
    lines.append("")
    lines.append("[cache]")
    lines.append(f'dir = "{config.cache_dir}"')
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
