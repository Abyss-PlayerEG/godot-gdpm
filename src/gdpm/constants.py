"""Shared constants for gdpm."""

from __future__ import annotations

from pathlib import Path

CONFIG_FILENAME = "gdproject.toml"
LOCK_FILENAME = "gdpm.lock"
TAG_FILENAME = "tag.gdpm"
LOCAL_TAG_PREFIX = "local+"
LOCAL_DIR_NAME = "gdpm-local"
HASHES_FILE = ".hashes"

REPO_URL = "https://github.com/Abyss-PlayerEG/godot-gdpm"
ISSUES_URL = "https://github.com/Abyss-PlayerEG/godot-gdpm/issues"
GITHUB_API_URL = "https://api.github.com/repos/Abyss-PlayerEG/godot-gdpm/"
GODOT_RELEASES_URL = "https://api.github.com/repos/godotengine/godot/releases"


def get_github_token() -> str:
    """Read GitHub token from ~/.gdpm/github_token.txt."""
    token_path = Path.home() / ".gdpm" / "github_token.txt"
    if not token_path.exists():
        return ""

    try:
        return token_path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def get_github_headers() -> dict[str, str]:
    """Get headers for GitHub API requests."""
    token = get_github_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


GODOT_DOWNLOAD_URL = "https://github.com/godotengine/godot/releases/download"
