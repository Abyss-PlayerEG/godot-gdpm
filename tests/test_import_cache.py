"""
gdpm import 的缓存根测试.

Store 导入必须走全局 cache_dir 配置 (与 sync/add 同一个缓存);
此前硬编码项目内 .gdpm/cache, cache info/clean 看不见导入的下载.
"""

from __future__ import annotations

from pathlib import Path

from gdpm.cli.commands.import_cmd import _store_import_cache
from gdpm.config.global_config import GlobalConfig


def test_store_import_cache_follows_config(monkeypatch) -> None:
    monkeypatch.setattr(
        "gdpm.cli.commands.import_cmd.read_global_config",
        lambda: GlobalConfig(cache_dir="/tmp/probe-cache"),
    )
    assert _store_import_cache().path == Path("/tmp/probe-cache") / "downloads"


def test_store_import_cache_default(monkeypatch) -> None:
    """未配置时回退默认目录 (不依赖真实用户配置)."""
    monkeypatch.setattr(
        "gdpm.cli.commands.import_cmd.read_global_config",
        lambda: GlobalConfig(),
    )
    assert _store_import_cache().path == Path.home() / ".gdpm" / "cache" / "downloads"
