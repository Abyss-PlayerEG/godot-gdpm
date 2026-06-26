"""Local engines configuration management."""

from __future__ import annotations

import json
from pathlib import Path


def get_config_path() -> Path:
    """Get path to local-engines.json."""
    return Path.home() / ".gdpm" / "local-engines.json"


def load_local_engines() -> dict[str, str]:
    """Load local engines config.

    Returns:
        Dict of {name: path}
    """
    path = get_config_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def save_local_engines(engines: dict[str, str]) -> None:
    """Save local engines config."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(engines, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_local_engine(name: str, path: str) -> None:
    """Add a local engine to config."""
    engines = load_local_engines()
    engines[name] = path
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


def get_local_engine(name: str) -> str | None:
    """Get local engine path by name.

    Returns:
        Path string or None if not found.
    """
    return load_local_engines().get(name)
