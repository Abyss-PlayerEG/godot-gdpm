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

## 用户目录（~/.gdpm）

gdpm 的全部运行时数据集中在一个目录：

| 路径 | 用途 |
|------|------|
| `~/.gdpm/config.toml` | 全局配置（见下节） |
| `~/.gdpm/cache/` | 下载缓存——默认位置，可用 `cache_dir` 迁移 |
| `~/.gdpm/engines/` | 已安装的 Godot 引擎（`gdpm godot install`） |
| `~/.gdpm/local-engines.json` | 用 `gdpm godot add` 手动注册的本地引擎 |

- 旧安装遗留的配置文件（platformdirs 位置）会在首次运行时自动迁移至此。
- 卸载 gdpm 只会移除可执行文件和 PATH 条目——`~/.gdpm` 下的一切都会保留。
- `cache/` 可随时删除（按需重新下载）；其余内容建议保留。

## 全局配置

`~/.gdpm/config.toml` 保存机器级默认值。推荐用命令行编辑：

```bash
gdpm config set parallel_downloads 8      # 下载并发数（1-32）
gdpm config set default_engine steam-godot@4.7-stable
gdpm config set cache_dir "~/gdpm-cache"   # 展开 ~；空值重置
gdpm config set language zh                # 帮助语言：en / zh
gdpm config open                           # 打开配置所在目录
```

文件本身：

```toml
[defaults]
godot_path = "godot"
addons_dir = "addons"
parallel_downloads = 4
default_engine = ""

[store]
base_url = "https://store.godotengine.org/api/v1"

[cache]
dir = ""

[ui]
language = "en"
```

`gdpm config set` 管理四个键：`parallel_downloads`、`default_engine`、
`cache_dir`、`language`（传空值恢复默认）。`godot_path`、`addons_dir` 与
`store.base_url` 虽会出现在文件中，但属于保留键——gdpm 暂未消费。
