# GDPM CLI 功能设计

> 基于官方 Godot Store API（`store.godotengine.org/api/v1`）

---

## 命令总览

```
gdpm <command> [args] [options]
```

| 命令 | 说明 | 优先级 |
|------|------|--------|
| `init` | 初始化项目 | MVP |
| `add` | 添加插件 | MVP |
| `remove` | 移除插件 | MVP |
| `sync` | 同步 addons/ | MVP |
| `list` | 列出插件 | MVP |
| `lock` | 生成锁文件 | MVP |
| `search` | 搜索插件 | Phase 2 |
| `info` | 插件详情 | Phase 2 |
| `update` | 更新插件 | Phase 2 |
| `tree` | 依赖树 | Phase 2 |
| `run` | 运行脚本 | Phase 3 |
| `export` | 导出清单 | Phase 3 |
| `config` | 管理配置 | Phase 3 |
| `doctor` | 诊断问题 | Phase 3 |

---

## 1. `gdpm init`

初始化项目，生成 `gdproject.toml`。

### 用法

```bash
gdpm init [name] [options]
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `name` | 项目名称 | 当前目录名 |

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--godot <ver>` | Godot 版本约束 | `>=4.0` |
| `--as-plugin` | 初始化为插件项目 | `false` |
| `--license <id>` | SPDX 许可证 | `MIT` |

### 行为

1. 检测当前目录是否已有 `project.godot`
   - 有 → 读取项目名和 Godot 版本
   - 无 → 使用参数 name
2. 生成 `gdproject.toml`
3. 如果 `addons/` 不存在 → 创建

### 输出

```
✓ Initialized gdproject in /path/to/project
  Created gdproject.toml
  Created addons/
```

### 错误

| 场景 | 退出码 | 输出 |
|------|--------|------|
| `gdproject.toml` 已存在 | 1 | `Error: gdproject.toml already exists. Use --force to overwrite.` |
| 目录不可写 | 1 | `Error: Permission denied` |

---

## 2. `gdpm add`

添加插件到项目。

### 用法

```bash
gdpm add <plugin>[@version] [options]
gdpm add <plugin1> <plugin2> ...    # 批量添加
```

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `plugin` | 插件名（slug） | `limbo-ai` |
| `@version` | 版本约束（可选） | `@1.5.0`、`@^1.0.0` |

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--dev` | 添加为开发依赖 | `false` |
| `--git <url>` | 从 Git 仓库添加 | - |
| `--path <path>` | 从本地路径添加 | - |
| `--no-sync` | 仅更新配置，不安装 | `false` |

### 行为

```
1. 解析参数 → 插件名 + 版本约束
2. 查询官方 Store API → 获取插件信息
   GET /api/v1/assets/{publisher}/{slug}/
3. 获取可用版本
   GET /api/v1/releases/{publisher}/{slug}/
4. 版本解析 → 满足约束的最新版本
5. 下载插件 zip → 解压到 addons/{name}/
6. 读取插件元数据（gdproject.toml / plugin.cfg）
   → 检查是否有子依赖
   → 如有 → 递归安装子依赖
7. 更新 gdproject.toml（写入依赖声明）
8. 更新 gdpm.lock（写入精确版本 + checksum）
```

### 输出

```
Resolving limbo-ai@>=1.5.0...
  Found limbo-ai v1.5.0 (latest)
Downloading limbo-ai v1.5.0...
  ████████████████████████████████ 100%
Installing to addons/limbo-ai...
  No sub-dependencies.
✓ Added limbo-ai v1.5.0
  Updated gdproject.toml
  Updated gdpm.lock
```

### 多依赖输出

```
Resolving 3 plugins...
  limbo-ai v1.5.0 ✓
  phantom-camera v4.3.0 ✓
  gdunit4 v1.0.0 ✓ (dev)
Downloading...
  limbo-ai        ████████████████████ 100%
  phantom-camera  ████████████████████ 100%
  gdunit4         ████████████████████ 100%
Installing...
  addons/limbo-ai ✓
  addons/phantom-camera ✓
  addons/gdunit4 ✓
✓ Added 3 plugins
```

### 子依赖输出

```
Resolving limbo-ai@>=1.5.0...
  Found limbo-ai v1.5.0
  Found dependency: gut >=9.0.0
  Found gut v9.2.0
Downloading...
  limbo-ai  ████████████████████ 100%
  gut       ████████████████████ 100%
Installing...
  addons/limbo-ai ✓
  addons/gut ✓
✓ Added limbo-ai v1.5.0 with 1 sub-dependency (gut v9.2.0)
```

### 错误

| 场景 | 退出码 | 输出 |
|------|--------|------|
| 插件不存在 | 1 | `Error: Plugin "xxx" not found in Godot Store` |
| 版本不存在 | 1 | `Error: No version of "limbo-ai" satisfies >=9.9.0` |
| 版本冲突 | 1 | `Error: Version conflict: ...` |
| 网络错误 | 1 | `Error: Failed to download: Connection timeout` |
| 无 gdproject.toml | 1 | `Error: Not a gdpm project. Run 'gdpm init' first.` |

---

## 3. `gdpm remove`

移除插件。

### 用法

```bash
gdpm remove <plugin> [options]
gdpm remove <plugin1> <plugin2> ...
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--recursive` | 同时移除不再需要的子依赖 | `false` |

### 行为

```
1. 检查插件是否在 gdproject.toml 中声明
2. 删除 addons/{name}/ 目录
3. 更新 gdproject.toml（移除依赖声明）
4. 更新 gdpm.lock
5. 如果 --recursive → 检查子依赖是否被其他插件需要
   → 不需要 → 一并移除
```

### 输出

```
Removing limbo-ai v1.5.0...
  Deleted addons/limbo-ai/
  Removed from gdproject.toml
  Updated gdpm.lock
✓ Removed limbo-ai
```

### --recursive 输出

```
Removing limbo-ai v1.5.0...
  Deleted addons/limbo-ai/
  Checking sub-dependencies...
    gut v9.2.0 — not required by other plugins
  Deleted addons/gut/
  Removed from gdproject.toml
  Updated gdpm.lock
✓ Removed limbo-ai and 1 sub-dependency (gut)
```

---

## 4. `gdpm sync`

同步 `addons/` 目录到 `gdpm.lock` 状态。

### 用法

```bash
gdpm sync [options]
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--frozen` | 严格按 lock 文件安装，不允许更新 | `false` |
| `--no-cache` | 不使用本地缓存 | `false` |
| `--dry-run` | 仅预览，不实际修改 | `false` |
| `--concurrency <n>` | 并行下载数 | `4` |

### 行为

```
1. 读取 gdproject.toml → 声明的依赖
2. 读取 gdpm.lock → 锁定的版本
3. 扫描 addons/ → 当前已安装的
4. 计算差异：
   - 需要安装的（声明了但未安装）
   - 需要移除的（addons/ 中有但未声明）
   - 版本不对的（已安装版本 ≠ lock 版本）
5. 执行：下载缺失的、删除多余的、更新版本不对的
```

### 输出（有变更）

```
Comparing gdpm.lock with addons/...
  Install: phantom-camera v4.3.0
  Install: gdunit4 v1.0.0 (dev)
  Remove:  old-plugin v0.1.0
  Update:  limbo-ai v1.4.0 → v1.5.0
Downloading 2 plugins...
  phantom-camera  ████████████████████ 100%
  gdunit4         ████████████████████ 100%
Installing...
  addons/phantom-camera ✓
  addons/gdunit4 ✓
Removing...
  addons/old-plugin ✓
Updating...
  addons/limbo-ai ✓
✓ Sync complete: 2 installed, 1 removed, 1 updated
```

### 输出（无变更）

```
Comparing gdpm.lock with addons/...
✓ Everything is up to date. Nothing to do.
```

### --frozen 模式（CI）

```
Reading gdpm.lock...
Installing 5 plugins (frozen mode)...
  limbo-ai        ████████████████████ 100%
  phantom-camera  ████████████████████ 100%
  dialogic        ████████████████████ 100%
  yatl            ████████████████████ 100%
  gut             ████████████████████ 100%
✓ Installed 5 plugins from lock file
```

### --dry-run 输出

```
Comparing gdpm.lock with addons/...
  Would install: phantom-camera v4.3.0
  Would remove:  old-plugin v0.1.0
✓ Dry run complete. 2 changes would be made.
```

---

## 5. `gdpm list`

列出已安装的插件。

### 用法

```bash
gdpm list [options]
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--outdated` | 仅显示有更新的插件 | `false` |
| `--json` | JSON 格式输出 | `false` |

### 输出（默认）

```
Project: my-game v0.1.0 (Godot >=4.2.0)

Dependencies (3):
  limbo-ai          v1.5.0    (latest: v1.5.0)
  phantom-camera    v4.3.0    (latest: v4.3.0)
  dialogic          v2.0.0    (latest: v2.1.0) ⬆

Dev Dependencies (1):
  gdunit4           v1.0.0    (latest: v1.0.0)

Use `gdpm tree` to see dependency relationships.
```

### --outdated 输出

```
Outdated plugins:
  dialogic    v2.0.0 → v2.1.0
  limbo-ai    v1.4.0 → v1.5.0

Run `gdpm update` to update all, or `gdpm update <name>` for specific.
```

---

## 6. `gdpm lock`

解析依赖并生成/更新 `gdpm.lock`。

### 用法

```bash
gdpm lock [options]
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--check` | 检查 lock 文件是否最新 | `false` |

### 行为

```
1. 读取 gdproject.toml
2. 递归解析所有依赖（调用 Store API + 插件仓库）
3. SAT 求解最优版本组合
4. 写入 gdpm.lock
```

### 输出

```
Resolving dependencies...
  limbo-ai >=1.5.0 → v1.5.0
  phantom-camera ^4.3.0 → v4.3.0
  dialogic 2.0.0 → v2.0.0
    └─ yatl * → v1.0.0
    └─ filesystem-dock-plus * → v0.3.0
  gdunit4 ^1.0.0 → v1.0.0 (dev)
✓ Lock file updated: 5 packages
```

### --check 输出（最新）

```
Checking lock file...
✓ gdpm.lock is up to date.
```

### --check 输出（过期）

```
Checking lock file...
✗ gdpm.lock is out of date.
  dialogic: locked v2.0.0, but ^2.0.0 resolves to v2.1.0
Run `gdpm lock` to update.
```

---

## 7. `gdpm search`

搜索插件（调用官方 Store API）。

### 用法

```bash
gdpm search <query> [options]
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--category <cat>` | 分类过滤 | - |
| `--license <id>` | 许可证过滤 | - |
| `--sort <field>` | 排序（relevance/updated/reviews） | `relevance` |
| `--limit <n>` | 结果数量 | `20` |
| `--json` | JSON 格式 | `false` |

### API 调用

```
GET /api/v1/search/query/?
  query=<query>
  type=0
  sort=<sort>
  licenses=<license>
  batch_size=<limit>
```

### 输出

```
Search results for "state machine" (6 found):

  limbo-ai                    v1.5.0    ⭐ 320
    AI framework: behavior trees, state machines, utility AI
    License: MIT  |  Author: limofeus

  state-machine               v1.2.0    ⭐ 85
    Simple state machine implementation for Godot 4
    License: MIT  |  Author: godot-addons

  quest-engine                v0.9.0    ⭐ 42
    Quest and dialogue state machine for RPGs
    License: MIT  |  Author: rpg-tools

  ... and 3 more. Use --limit 50 to see all.
```

---

## 8. `gdpm info`

查看插件详情。

### 用法

```bash
gdpm info <plugin>
```

### API 调用

```
GET /api/v1/assets/{publisher}/{slug}/
GET /api/v1/releases/{publisher}/{slug}/
```

### 输出

```
limbo-ai v1.5.0
────────────────────────────────────
AI framework for Godot 4: behavior trees, state machines, utility AI

Author:     limofeus
License:    MIT
Homepage:   https://github.com/limofeus/limbo-ai
Godot:      >=4.2.0
Tags:       ai, behavior-tree, state-machine

Installed:  v1.5.0 (latest)
Dependency: None

Versions:
  v1.5.0  2026-06-15  (latest)
  v1.4.0  2026-05-20
  v1.3.0  2026-04-10
  v1.2.0  2026-03-01
  v1.1.0  2026-01-15
  v1.0.0  2025-12-01
```

---

## 9. `gdpm update`

更新插件。

### 用法

```bash
gdpm update [plugin] [options]
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--latest` | 忽略 gdproject.toml 约束，直接更新到最新 | `false` |
| `--dry-run` | 仅预览 | `false` |

### 行为

```
1. 检查当前版本 vs 最新版本（Store API）
2. 检查是否满足 gdproject.toml 中的约束
3. 下载新版本 → 替换 addons/{name}/
4. 更新 gdproject.toml + gdpm.lock
```

### 输出（全部更新）

```
Checking for updates...
  limbo-ai        v1.4.0 → v1.5.0 ✓
  phantom-camera  v4.3.0 (up to date)
  dialogic        v2.0.0 → v2.1.0 ✓
Downloading 2 updates...
  limbo-ai        ████████████████████ 100%
  dialogic        ████████████████████ 100%
✓ Updated 2 plugins
```

### 输出（指定插件）

```
Updating limbo-ai...
  v1.4.0 → v1.5.0
  Downloading... ████████████████████ 100%
✓ Updated limbo-ai to v1.5.0
```

---

## 10. `gdpm tree`

显示依赖树。

### 用法

```bash
gdpm tree [options]
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--depth <n>` | 最大深度 | 无限制 |
| `--json` | JSON 格式 | `false` |

### 输出

```
my-game v0.1.0
├── limbo-ai v1.5.0
├── phantom-camera v4.3.0
└── dialogic v2.0.0
    ├── yatl v1.0.0
    └── filesystem-dock-plus v0.3.0

dev:
└── gdunit4 v1.0.0
```

---

## 11. `gdpm run`

运行 `gdproject.toml` 中定义的脚本，或直接运行 Godot。

### 用法

```bash
gdpm run <script> [args...]
gdpm run godot [-- <godot-args>]
```

### 行为

```
1. 读取 gdproject.toml 的 [scripts] 段
2. 执行对应的命令
3. 如果是 godot → 使用全局配置中的 godot_path
```

### 示例

```bash
gdpm run test        # 执行 [scripts] test = "godot --headless ..."
gdpm run build       # 执行 [scripts] build = "godot --headless --export..."
gdpm run godot       # 直接运行 Godot
gdpm run godot -- --editor  # 打开编辑器
```

### 输出

```
Running script 'test'...
godot --headless --script res://tests/run_tests.gd
[Godot output...]
✓ Script 'test' completed (exit code 0)
```

---

## 12. `gdpm config`

管理全局配置。

### 用法

```bash
gdpm config get <key>
gdpm config set <key> <value>
gdpm config list
```

### 示例

```bash
gdpm config get godot_path
# /usr/local/bin/godot

gdpm config set godot_path /opt/godot/godot
# ✓ Set godot_path = /opt/godot/godot

gdpm config list
# godot_path = /opt/godot/godot
# addons_dir = addons
# parallel_downloads = 4
```

---

## 13. `gdpm doctor`

诊断项目健康状态。

### 用法

```bash
gdpm doctor
```

### 输出

```
GDPM Doctor — checking project health...

✓ gdproject.toml exists and is valid
✓ gdpm.lock exists and is up to date
✓ All declared plugins are installed
✓ No version conflicts detected
⚠ gdunit4 v1.0.0 has a newer version (v1.1.0)
✗ limbo-ai/plugin.cfg not found — plugin may be corrupted

Found 1 issue, 1 warning.
Run `gdpm sync` to fix missing plugins.
```

---

## 全局选项

所有命令通用：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--help` | 显示帮助 | - |
| `--version` | 显示版本 | - |
| `--verbose` | 详细输出 | `false` |
| `--quiet` | 静默模式 | `false` |
| `--no-color` | 禁用颜色 | `false` |

---

## 退出码

| 代码 | 含义 |
|------|------|
| 0 | 成功 |
| 1 | 一般错误（插件不存在、版本冲突等） |
| 2 | 参数错误 |
| 3 | 网络错误 |
| 4 | 文件系统错误 |
| 5 | 锁文件过期（`gdpm lock --check`）

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `GDPM_GODOT_PATH` | Godot 可执行文件路径 | `godot` |
| `GDPM_CONCURRENCY` | 并行下载数 | `4` |
| `GDPM_CACHE_DIR` | 缓存目录 | `~/.cache/gdpm` |
| `GDPM_NO_COLOR` | 禁用颜色 | `false` |
| `GDPM_STORE_URL` | 自定义 Store API 地址 | `https://store.godotengine.org/api/v1` |

---

## 配置优先级

```
环境变量 > 命令行选项 > gdproject.toml > 全局配置 > 默认值
```
