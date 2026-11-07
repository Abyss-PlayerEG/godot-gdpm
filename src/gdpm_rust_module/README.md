# gdpm_rust_module

gdpm 的原生工具模块（Rust / PyO3），为热点路径提供可选加速。

- 独立 maturin 子项目，**gdpm 主包构建链（hatchling）零改动**
- 未构建时 gdpm 侧 `import` 失败即回退纯 Python 实现（优雅降级）
- wheel 不会进 gdpm 主包（hatch `packages = ["src/gdpm"]` 显式限定）

## 布局

```
src/gdpm_rust_module/
├── pyproject.toml        # maturin 构建后端, 发行名 gdpm-rust-module
├── Cargo.toml            # [lib] 使用 Cargo 默认源码位置 src/lib.rs
├── src/lib.rs            # Rust 源码 (标准 Cargo 布局), 每个功能一个 #[pyfunction]
└── target/               # 构建产物 (已 gitignore)
```

> 完整路径 `src/gdpm_rust_module/src/lib.rs` 看似"src 套 src"，
> 实为嵌套 crate 的正常形态：Cargo 只以本目录为包根，与外层 Python 的 `src/` 互不可见。

三个名字的对应（易错）：

| 场合 | 名字 |
|------|------|
| 目录 / import | `gdpm_rust_module`（下划线） |
| wheel / 发行名 | `gdpm-rust-module`（连字符） |
| `#[pymodule]` 函数名 | 必须与 `[lib] name` 一致，否则 import 报错 |

## 构建与安装

```bash
# 在仓库根目录执行 (maturin 在 dev 依赖组)
.venv/bin/maturin build --release --manifest-path src/gdpm_rust_module/Cargo.toml \
  || (cd src/gdpm_rust_module && ../../.venv/bin/maturin build --release)

uv pip install src/gdpm_rust_module/target/wheels/*.whl

# 冒烟
uv run python -c "import gdpm_rust_module; print(gdpm_rust_module.add(1, 2))"
uv run pytest tests/test_rust_module.py -q
```

日常开发（改完 Rust 重新装）：

```bash
cd src/gdpm_rust_module && ../../.venv/bin/maturin build --release
cd ../.. && uv pip install src/gdpm_rust_module/target/wheels/*.whl
```

## 注意事项

1. **不要在本目录里跑 `uv run`**——uv 会认这个嵌套 pyproject 并自建空 venv
   （maturin 在根 venv 里，会报 `Failed to spawn: maturin`）。构建一律用根 venv 的二进制。
2. **`uv sync` 可能剔除本模块**——它不在根 lockfile 里；被剔除后按上面命令重装即可。
   （若将来要长期绑定，可改为根 pyproject 的 path 依赖，代价是每次 sync 都要编译。）
3. 提交时一并带上 `Cargo.lock`（cdylib 应锁定依赖版本）。
4. 新增工具函数：在 `src/lib.rs` 写 `#[pyfunction]` → 在 `#[pymodule]` 注册 →
   重建安装 → gdpm 侧 `import gdpm_rust_module` 使用；类型存根可用 `pyo3-stubgen` 生成。
