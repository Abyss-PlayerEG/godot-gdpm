"""
gdpm godot add 的覆盖确认提示测试.

click.confirm 不渲染 rich 标记 —— 覆盖确认曾显示字面 [yellow];
改用 rich Confirm 后标记正常渲染 (文案按控制台决策保持英文).
"""

from __future__ import annotations

from click.testing import CliRunner

from gdpm.cli.commands.godot.engine import godot_add
from gdpm.config.local_engines import LocalEngine


def test_overwrite_prompt_renders_markup(tmp_path, monkeypatch) -> None:
    """覆盖确认: 标记被渲染而非字面显示, 拒绝后不写注册表."""
    target = tmp_path / "Godot.app"
    target.mkdir()
    monkeypatch.setattr("gdpm.utils.godot.detect_godot_binary", lambda path: target)
    monkeypatch.setattr(
        "gdpm.utils.godot.get_godot_version", lambda binary: "4.7-stable"
    )
    monkeypatch.setattr(
        "gdpm.config.local_engines.load_local_engines",
        lambda: {"x": LocalEngine(path="/other", version="4.7-stable")},
    )

    result = CliRunner().invoke(godot_add, [str(target), "--name", "x"], input="n\n")

    assert result.exit_code == 0
    assert "'x' already exists" in result.output
    assert "[yellow]" not in result.output
