"""
click 命令参数绑定回归测试.

背景: godot_use 曾因 @click.argument("id") 与签名 engine_id 不匹配,
每次真实调用都 TypeError —— 静态扫描 + 实际调用双重防护.
"""

from __future__ import annotations

import ast
from pathlib import Path

from click.testing import CliRunner

from gdpm.cli.commands.godot import engine as engine_mod

CLI_ROOT = Path(__file__).resolve().parent.parent / "src" / "gdpm" / "cli"


def _declared_params(decorator: ast.Call) -> set[str]:
    """提取单个 click 装饰器声明的参数名."""
    fn = decorator.func
    attr = fn.attr if isinstance(fn, ast.Attribute) else ""
    names: set[str] = set()

    if attr == "argument":
        for a in decorator.args:
            if (
                isinstance(a, ast.Constant)
                and isinstance(a.value, str)
                and not a.value.startswith("-")
            ):
                names.add(a.value)
                break
    elif attr == "option":
        expose = next(
            (
                kw.value.value
                for kw in decorator.keywords
                if kw.arg == "expose_value"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, bool)
            ),
            True,
        )
        if not expose:
            # expose_value=False 的选项不进入函数参数
            return names
        explicit = next(
            (
                a.value
                for a in decorator.args
                if isinstance(a, ast.Constant)
                and isinstance(a.value, str)
                and not a.value.startswith("-")
            ),
            None,
        )
        if explicit:
            names.add(explicit)
        else:
            for a in decorator.args:
                if (
                    isinstance(a, ast.Constant)
                    and isinstance(a.value, str)
                    and a.value.startswith("--")
                ):
                    names.add(a.value.lstrip("-").replace("-", "_"))
                    break
    return names


def test_click_params_match_function_signatures() -> None:
    """全部 CLI 命令: click 声明的参数名必须存在于函数签名中."""
    issues: list[str] = []

    for f in sorted(CLI_ROOT.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            declared: set[str] = set()
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    declared |= _declared_params(dec)
            sig = {a.arg for a in node.args.args + node.args.kwonlyargs}
            extra = declared - sig
            if extra:
                rel = f.relative_to(CLI_ROOT.parent.parent)
                issues.append(
                    f"{rel}:{node.lineno} {node.name}() 声明 {sorted(extra)}"
                    f" 但签名只有 {sorted(sig)}"
                )

    assert not issues, "click 参数与函数签名不匹配:\n" + "\n".join(issues)


def test_use_command_binds_argument(monkeypatch) -> None:
    """godot_use 实际调用不再 TypeError (参数绑定回归)."""
    monkeypatch.setattr(engine_mod, "find_engine", lambda name, version: None)

    result = CliRunner().invoke(engine_mod.godot_use, ["no-such-engine@1.0"])

    assert not isinstance(result.exception, TypeError), (
        f"参数绑定失败: {result.exception}"
    )
    assert result.exit_code == 0
    assert "not found" in result.output
