"""
gdpm godot open 按 ID 启动测试.

open 支持可选 ID (Name@Version) 一次性指定引擎: 不读项目配置、
不写任何配置; 非法格式与不存在的引擎被拒绝且不启动进程.
"""

from __future__ import annotations

import json

from click.testing import CliRunner

from gdpm.cli.commands.godot.open import godot_open


class _FakeProc:
    """Popen 替身: wait 返回 None 表示启动成功仍在运行."""

    def wait(self, timeout: float | None = None) -> None:
        return None


def _no_launch(*args: object, **kwargs: object) -> object:
    raise AssertionError("process should not be launched")


def test_open_by_id_launches_resolved_engine(tmp_path, monkeypatch) -> None:
    """显式 ID: 经 resolve_engine_id 解析并启动, 完全跳过项目配置."""
    conf = tmp_path / ".engines-conf.json"
    conf.write_text(
        json.dumps(
            {"godot": {"name": "conf-engine", "version": "1.0", "path": "/conf/Godot"}}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.open.find_project_root", lambda: tmp_path
    )
    captured: dict[str, str] = {}

    def _resolve(engine_id: str, *, example: str) -> tuple[str, str, str]:
        captured.update(engine_id=engine_id, example=example)
        return ("gdpm-godot", "4.7-stable-csharp", "/resolved/Godot")

    monkeypatch.setattr("gdpm.cli.commands.godot.open.resolve_engine_id", _resolve)
    launched: dict[str, list[str]] = {}
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.open.subprocess.Popen",
        lambda args, **kwargs: launched.update(args=args) or _FakeProc(),
    )

    result = CliRunner().invoke(godot_open, ["gdpm-godot@4.7-stable-csharp"])

    assert result.exit_code == 0
    assert "Opening gdpm-godot@4.7-stable-csharp" in result.output
    assert "Opened gdpm-godot@4.7-stable-csharp" in result.output
    # ID 与示例原样传递 (C# 后缀不丢), 解析优先于项目配置
    assert captured["engine_id"] == "gdpm-godot@4.7-stable-csharp"
    assert "gdpm godot open" in captured["example"]
    assert launched["args"][0] == "/resolved/Godot"
    assert "-e" in launched["args"]
    assert str(tmp_path) in launched["args"]


def test_open_invalid_id_format_rejected(monkeypatch) -> None:
    """缺 @ 的输入按 Name@Version 格式拒绝, 不启动进程."""
    monkeypatch.setattr("gdpm.cli.commands.godot.open.subprocess.Popen", _no_launch)

    result = CliRunner().invoke(godot_open, ["4.7-stable"])

    assert result.exit_code == 0
    assert "Invalid format" in result.output
    assert "Name@Version" in result.output
    # 示例命令带本命令上下文
    assert "gdpm godot open gdpm-godot@4.7-stable" in result.output


def test_open_unknown_engine_rejected(monkeypatch) -> None:
    """find_engine 找不到的引擎拒绝启动, 并提示 list -id."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.find_engine", lambda name, version: None
    )
    monkeypatch.setattr("gdpm.cli.commands.godot.open.subprocess.Popen", _no_launch)

    result = CliRunner().invoke(godot_open, ["ghost@9.9"])

    assert result.exit_code == 0
    assert "not found" in result.output
    assert "list -id" in result.output


def test_open_without_id_uses_project_conf(tmp_path, monkeypatch) -> None:
    """无 ID 时保持原行为: 走项目 .engines-conf.json, 不碰 find_engine."""
    conf = tmp_path / ".engines-conf.json"
    conf.write_text(
        json.dumps(
            {"godot": {"name": "conf-engine", "version": "1.0", "path": "/conf/Godot"}}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.open.find_project_root", lambda: tmp_path
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.find_engine",
        lambda name, version: (_ for _ in ()).throw(AssertionError("unused")),
    )
    launched: dict[str, list[str]] = {}
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.open.subprocess.Popen",
        lambda args, **kwargs: launched.update(args=args) or _FakeProc(),
    )

    result = CliRunner().invoke(godot_open, [])

    assert result.exit_code == 0
    assert "Opening conf-engine@1.0" in result.output
    assert launched["args"][0] == "/conf/Godot"
