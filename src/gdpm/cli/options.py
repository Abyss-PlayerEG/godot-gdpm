"""Shared CLI options and decorators."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from collections.abc import Callable


def yes_option[**P, T](func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to add -y/--yes option to a command.

    Usage:
        @click.command()
        @yes_option
        def my_command(yes: bool) -> None:
            if yes:
                # Skip prompts
                ...
    """
    return click.option(
        "-y",
        "--yes",
        is_flag=True,
        default=False,
        help="Skip all confirmation prompts.",
    )(func)
