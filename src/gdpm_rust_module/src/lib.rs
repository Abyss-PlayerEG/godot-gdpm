//! gdpm 原生工具模块 / gdpm native tool module.
//!
//! 通过 PyO3 暴露给 Python, 供 gdpm 按需加速热点路径.
//! 后续工具函数按模块追加: 每个功能一个 `#[pyfunction]`,
//! 在 `#[pymodule]` 中注册即可.

use pyo3::prelude::*;

/// 返回原生模块版本号 / Return the native module version.
#[pyfunction]
fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// 示例函数: 两数相加, 验证类型转换链路 / Example: add two integers.
#[pyfunction]
fn add(a: i64, b: i64) -> i64 {
    a + b
}

#[pymodule]
fn gdpm_rust_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(add, m)?)?;
    Ok(())
}
