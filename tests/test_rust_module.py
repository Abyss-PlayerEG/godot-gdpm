"""
原生工具模块冒烟测试.

未构建原生模块时整体跳过 (importorskip);
构建方式见 src/gdpm_rust_module/README.md.
"""

from __future__ import annotations

import pytest

gdpm_rust_module = pytest.importorskip(
    "gdpm_rust_module", reason="原生模块未构建 (见 src/gdpm_rust_module/README.md)"
)


def test_version_reports_nonempty() -> None:
    assert gdpm_rust_module.version()


def test_add_type_conversion() -> None:
    """i64 <-> int 转换链路正常."""
    assert gdpm_rust_module.add(2, 3) == 5
    assert gdpm_rust_module.add(-1, 1) == 0
