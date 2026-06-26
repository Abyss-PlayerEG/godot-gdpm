"""Local engines configuration management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LocalEngine:
    path: str
    version: str = ""


def get_config_path() -> Path:
    """Get path to local-engines.json."""
    return Path.home() / ".gdpm" / "local-engines.json"


def load_config() -> dict:
    """Load raw config dict."""
    path = get_config_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def save_config(config: dict) -> None:
    """Save raw config dict."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_local_engines() -> dict[str, LocalEngine]:
    """Load local engines config.

    Returns:
        Dict of {name: LocalEngine}
    """
    config = load_config()
    engines = config.get("engines", {})

    result: dict[str, LocalEngine] = {}
    for name, value in engines.items():
        if isinstance(value, str):
            # Legacy format: just a path string
            result[name] = LocalEngine(path=value)
        elif isinstance(value, dict):
            result[name] = LocalEngine(
                path=value.get("path", ""),
                version=value.get("version", ""),
            )
    return result


def save_local_engines(engines: dict[str, LocalEngine]) -> None:
    """Save local engines config."""
    config = load_config()
    config["engines"] = {
        name: {"path": eng.path, "version": eng.version}
        for name, eng in engines.items()
    }
    save_config(config)


def add_local_engine(name: str, path: str, version: str = "") -> None:
    """Add a local engine to config."""
    engines = load_local_engines()
    engines[name] = LocalEngine(path=path, version=version)
    save_local_engines(engines)


def remove_local_engine(name: str) -> bool:
    """Remove a local engine from config.

    Returns:
        True if removed, False if not found.
    """
    engines = load_local_engines()
    if name not in engines:
        return False
    del engines[name]
    save_local_engines(engines)
    return True


def get_local_engine(name: str) -> LocalEngine | None:
    """Get local engine by name.

    Returns:
        LocalEngine or None if not found.
    """
    return load_local_engines().get(name)


def get_default_engine() -> str:
    """Get default engine ID.

    Returns:
        Engine ID string (e.g., 'steam@4.7-stable'), or empty string.
    """
    config = load_config()
    return config.get("default", "")


def set_default_engine(engine_id: str) -> None:
    """Set default engine ID."""
    config = load_config()
    config["default"] = engine_id
    save_config(config)


def unset_default_engine() -> None:
    """Remove default engine setting."""
    config = load_config()
    config.pop("default", None)
    save_config(config)
