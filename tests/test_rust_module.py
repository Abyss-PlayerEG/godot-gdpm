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

# 源码树里的空目录会被解析成命名空间包 (import 成功但没有任何属性),
# importorskip 识别不了这种情况 —— 入口函数缺失即按设计整体跳过
if not hasattr(gdpm_rust_module, "version"):
    pytest.skip("原生模块未构建 (命名空间占位)", allow_module_level=True)


def test_version_reports_nonempty() -> None:
    assert gdpm_rust_module.version()


def test_add_type_conversion() -> None:
    """i64 <-> int 转换链路正常."""
    assert gdpm_rust_module.add(2, 3) == 5
    assert gdpm_rust_module.add(-1, 1) == 0
