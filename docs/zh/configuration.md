# 配置参考

## gdproject.toml

项目配置文件，类似 `pyproject.toml` / `Cargo.toml`。

```toml
[project]
name = "my-game"
version = "0.1.0"
godot = ">=4.7.0"
license = "MIT"

[dependencies]
limbo-ai = ">=1.5.0"
phantom-camera = "^4.3.0"

[dev-dependencies]
gdunit4 = "^1.0.0"

[scripts]
test = "godot --headless --script res://tests/run_tests.gd"
```

## 版本约束

| 语法 | 含义 | 示例 |
|------|------|------|
| `1.5.0` | 精确版本 | `limbo-ai = "1.5.0"` |
| `^1.5.0` | 兼容更新 | `>=1.5.0, <2.0.0` |
| `~1.5.0` | 补丁更新 | `>=1.5.0, <1.6.0` |
| `>=1.0.0` | 最低版本 | `>=1.0.0` |
| `*` | 任意版本 | `limbo-ai = "*"` |

## 文件说明

| 文件 | 用途 |
|------|------|
| `gdproject.toml` | 项目配置和依赖 |
| `gdpm.lock` | 锁文件，确保可复现安装 |
| `tag.gdpm` | 追踪 addon 归属哪个插件 |
| `.engines-conf.json` | 项目引擎配置 |
| `gdpm-local/` | 打包的本地插件 |
