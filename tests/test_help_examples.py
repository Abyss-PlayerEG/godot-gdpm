"""
帮助示例与选项定义一致性.

- 示例里出现的 --选项 必须真实存在 (抓拼写/过期选项).
- Choice 型选项的取值必须在 choices 内 (回归: search --sort downloads ——
  示例值不在自己的选项列表, 用户照抄必错).

----

Notes
----
- 遍历根命令组与全部子命令组 (godot/config/cache) 的 examples.
- 短选项与布尔选项不在校验范围 (无取值问题).
"""

from __future__ import annotations

import shlex

import click

from gdpm.cli.app import main


def _iter_commands(group: click.Group):
    """
    递归遍历命令组及其子命令组.

    ----

    Parameters
    ----
    group : click.Group
        根命令组.

    Returns
    ----
    Iterator[click.Command]
        深度优先的全部命令.
    """
    for cmd in group.commands.values():
        yield cmd
        if isinstance(cmd, click.Group):
            yield from _iter_commands(cmd)


def _resolve_target(root: click.Group, example: str) -> tuple[click.Command, list[str]]:
    """
    沿子命令路径定位示例真正执行的命令.

    ----

    Parameters
    ----
    root : click.Group
        根命令组.
    example : str
        示例命令行 (如 "gdpm godot list --remote").

    Returns
    ----
    tuple[click.Command, list[str]]
        目标命令与剩余待校验的 token 列表.
    """
    tokens = shlex.split(example)
    node: click.Command = root
    i = 1  # 跳过程序名
    while i < len(tokens) and isinstance(node, click.Group):
        sub = node.commands.get(tokens[i])
        if sub is None:
            break
        node = sub
        i += 1
    return node, tokens[i:]


def _find_param(
    target: click.Command, owner: click.Command, name: str
) -> click.Parameter | None:
    """在目标命令 (优先) 或示例所属命令上查找选项定义."""
    for scope in (target.params, owner.params):
        for p in scope:
            if name in p.opts or name in getattr(p, "secondary_opts", []):
                return p
    return None


def test_examples_reference_real_options_with_valid_choices() -> None:
    """示例引用的 --选项 必须存在, 且 Choice 取值必须合法."""
    problems: list[str] = []
    for owner in _iter_commands(main):
        for example, _label in getattr(owner, "examples", []):
            target, tokens = _resolve_target(main, example)
            for i, token in enumerate(tokens):
                if not token.startswith("--"):
                    continue
                name = token.split("=", 1)[0]
                param = _find_param(target, owner, name)
                if param is None:
                    problems.append(
                        f"{owner.name}: unknown option {name} in example: {example}"
                    )
                    continue
                if param.is_flag or not isinstance(param.type, click.Choice):
                    continue
                if "=" in token:
                    value = token.split("=", 1)[1]
                else:
                    if i + 1 >= len(tokens) or tokens[i + 1].startswith("-"):
                        problems.append(
                            f"{owner.name}: {name} needs a value in example: {example}"
                        )
                        continue
                    value = tokens[i + 1]
                if value not in param.type.choices:
                    problems.append(
                        f"{owner.name}: {name} {value!r} not in "
                        f"{param.type.choices} (example: {example})"
                    )
    assert not problems, "\n".join(problems)
