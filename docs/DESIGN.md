# GDPM — Godot Dependency Package Manager

> 版本: 0.2.0 | 状态: 设计中

---

## 1. 项目概述

**GDPM** 是一个 Godot 插件依赖管理 CLI 工具，对标 `uv`（Python）、`npm`（Node.js）、`cargo`（Rust）。

gdpm **不自建注册中心**，直接对接 [Godot Asset Store](https://store.godotengine.org) 官方 API。

### 1.1 解决什么问题

| 官方 Store 能做的 | 官方 Store 做不到的 |
|------------------|-------------------|
| 浏览/搜索插件 | 依赖自动解析 |
| 编辑器内安装 | 锁文件可复现 |
| 版本发布管理 | CLI 批量管理 |
| 评分/评论 | CI/CD 集成 |

gdpm 补足右侧：**依赖解析 + 锁文件 + CLI + CI/CD**。

### 1.2 核心原则

1. **零自建** — 不建 registry，不建网站，全靠官方 Store API
2. **声明式** — `gdproject.toml` 声明依赖，`gdpm sync` 实现状态
3. **可复现** — `gdpm.lock` 保证团队和 CI 使用相同版本
4. **非侵入** — 仅管理 `addons/` 目录，不改 Godot 项目文件

---

## 2. 数据源

### 2.1 Godot Asset Store API

官方 API 地址：`store.godotengine.org/api/v1/redoc`

gdpm 通过此 API 获取：
- 插件搜索
- 插件详情（名称、描述、作者、许可证）
- 版本列表
- 下载链接

### 2.2 插件仓库元数据

官方 Store 不提供依赖信息。gdpm 从插件的 GitHub 仓库获取：

```
插件仓库
├── plugin.cfg           # Godot 标准元数据
├── gdproject.toml       # gdpm 专属（可选，含依赖声明）
└── addons/{name}/
```

**gdpm 优先读取 `gdproject.toml`**，没有则回退到 `plugin.cfg`。

### 2.3 元数据获取流程

```
gdpm add limbo-ai
  │
  ├─ 1. 查官方 Store API → 获取基本信息、下载链接
  │
  ├─ 2. 下载插件 zip → 解压到临时目录
  │
  ├─ 3. 检查 gdproject.toml → 有则读取依赖声明
  │     没有 → 回退到 plugin.cfg → 读取基本元数据
  │
  ├─ 4. 自动分析 → 扫描 GDScript import 推断依赖（可选）
  │
  └─ 5. 安装到 addons/ → 写入 gdproject.toml + gdpm.lock
```

---

## 3. 命令设计

```
gdpm <command>

项目管理:
  init [name]          初始化项目（生成 gdproject.toml）
  sync                 根据 gdpm.lock 同步 addons/
  lock                 解析依赖并生成/更新 gdpm.lock
  status / st          查看插件状态和可用更新

依赖操作:
  add <plugin>[@ver]   添加插件
  remove / rm <plugin> 移除插件
  update / up [plugin] 更新插件
  list / ls            列出已安装插件
  tree                 显示依赖树
  search <query>       搜索插件（官方 Store API）
  info <plugin>        查看插件详情

高级:
  run <hook>           运行 gdproject.toml 中定义的钩子
  export               导出依赖清单（CI 用）
  config               管理全局配置
  doctor               诊断项目健康状态
```

### 3.1 常用命令示例

```bash
# 初始化
gdpm init my-game --godot 4.3

# 添加插件（从官方 Store）
gdpm add limbo-ai
gdpm add limbo-ai@1.5.0
gdpm add limbo-ai@">=1.0.0,<2.0.0"
gdpm add --dev gdunit4

# 从 Git 添加（官方 Store 没有的插件）
gdpm add --git https://github.com/user/plugin.git

# 移除
gdpm remove limbo-ai

# 同步（安装缺失的，移除多余的）
gdpm sync
gdpm sync --frozen       # CI 模式：严格按 lock 文件
gdpm sync --dry-run      # 预览

# 更新
gdpm update              # 全部
gdpm update limbo-ai     # 指定
gdpm update --latest     # 忽略约束

# 查看
gdpm list
gdpm tree
gdpm search "state machine"
gdpm info limbo-ai
```

---

## 4. 配置文件

### 4.1 `gdproject.toml` — 项目配置

```toml
[project]
name = "my-game"
version = "0.1.0"
description = "My Godot game"
godot = ">=4.2.0"
license = "MIT"
addons_dir = "addons"

[dependencies]
limbo-ai = ">=1.5.0"
phantom-camera = "^4.3.0"
dialogic = { version = "2.0.0" }
my-plugin = { git = "https://github.com/user/plugin.git", branch = "main" }
local-tool = { path = "../local-tool" }

[dev-dependencies]
gdunit4 = "^1.0.0"

[scripts]
test = "godot --headless --script res://tests/run_tests.gd"
build = "godot --headless --export-release ..."
```

### 4.2 版本约束语法

| 语法 | 含义 | 示例 |
|------|------|------|
| `1.5.0` | 精确版本 | `limbo-ai = "1.5.0"` |
| `^1.5.0` | 兼容更新 | `>=1.5.0, <2.0.0` |
| `~1.5.0` | 补丁更新 | `>=1.5.0, <1.6.0` |
| `>=1.0.0` | 最低版本 | `>=1.0.0` |
| `>=1.0.0,<2.0.0` | 范围 | 显式范围 |
| `*` | 任意版本 | `limbo-ai = "*"` |

### 4.3 `gdpm.lock` — 锁文件

```toml
version = 1

[[package]]
name = "limbo-ai"
version = "1.5.0"
source = "store+https://store.godotengine.org/asset/limofeus/limbo-ai"
checksum = "sha256:abc123..."
dependencies = []

[[package]]
name = "phantom-camera"
version = "4.3.0"
source = "store+https://store.godotengine.org/asset/ramokz/phantom-camera"
checksum = "sha256:def456..."
dependencies = []

[[package]]
name = "dialogic"
version = "2.0.0"
source = "store+https://store.godotengine.org/asset/dialogic-godot/dialogic"
checksum = "sha256:ghi789..."
dependencies = ["yatl", "filesystem-dock-plus"]
```

### 4.4 全局配置

位于 `~/.config/gdpm/config.toml`：

```toml
[defaults]
godot_path = "/usr/local/bin/godot"
addons_dir = "addons"
parallel_downloads = 4

[store]
base_url = "https://store.godotengine.org/api/v1"
# 自定义 Store（企业内部用）
# custom_store = "https://store.company.com/api/v1"

[cache]
dir = "~/.cache/gdpm"
max_size = "1GB"
```

---

## 5. 依赖解析

### 5.1 解析策略

```
输入: gdproject.toml 中的依赖声明
过程:
  1. 从官方 Store API 获取插件所有版本
  2. 检查插件仓库中的 gdproject.toml / plugin.cfg 获取依赖
  3. 递归解析传递依赖
  4. SAT 求解找到满足所有约束的最优解
输出: gdpm.lock
```

### 5.2 冲突处理

```bash
$ gdpm add plugin-a plugin-c

Error: Version conflict detected
  plugin-a requires lib-b ^1.0.0
  plugin-c requires lib-b ^2.0.0
  No version of lib-b satisfies both constraints

Suggestion:
  - Check if newer versions of plugin-a/plugin-c have compatible lib-b requirements
  - Use `gdpm tree` to inspect the dependency graph
```

### 5.3 Godot 版本兼容性

gdpm 同时检查：
1. 插件间的版本约束兼容性
2. 所有插件与项目声明的 Godot 版本兼容性

---

## 6. 目录结构

### 6.1 用户项目

```
my-game/
├── gdproject.toml       # 依赖配置（提交到 Git）
├── gdpm.lock            # 锁文件（提交到 Git）
├── project.godot        # Godot 项目文件
├── addons/              # 插件目录（可选提交）
│   ├── limbo-ai/
│   └── phantom-camera/
└── src/
```

### 6.2 `.gitignore` 推荐

```gitignore
# 策略 A：提交 addons/（小团队）
# 不忽略

# 策略 B：忽略 addons/（大团队/CI，依赖 gdpm sync）
addons/
```

---

## 7. GDExtension 支持

原生插件（`.gdextension`）包含平台特定二进制文件：

```
addons/my-native-plugin/
├── plugin.cfg
├── my-native-plugin.gdextension
├── bin/
│   ├── libmy_plugin.linux.x86_64.so
│   ├── libmy_plugin.windows.x86_64.dll
│   └── libmy_plugin.macos.framework
```

gdpm 处理策略：
1. **平台感知下载** — 仅下载当前平台的二进制
2. **多平台锁文件** — `gdpm.lock` 记录所有平台 checksum
3. **CI 交叉编译** — `gdpm sync --platform linux,windows`

```toml
# gdproject.toml
[platform]
targets = ["linux", "windows", "macos"]
```

---

## 8. CI/CD 集成

```yaml
# GitHub Actions
- name: Install Godot plugins
  run: |
    gdpm sync --frozen
    gdpm run test
```

---

## 9. 缓存

```
~/.cache/gdpm/
├── store/               # Store API 响应缓存（TTL 1h）
├── downloads/           # 插件包缓存（永久，按 checksum 去重）
└── index/               # 搜索索引缓存（TTL 24h）
```

---

## 10. 安全

- 所有下载的包通过 SHA256 校验
- `gdpm.lock` 记录每个包的 checksum
- `gdpm audit` 检查已知漏洞

---

## 11. 技术栈

| 组件 | 选型 |
|------|------|
| CLI | `click` |
| HTTP | `httpx` |
| TOML | `tomllib` |
| 版本 | `packaging` |
| 终端 | `rich` |
| 配置 | `platformdirs` |
| 测试 | `pytest` |

---

## 12. 路线图

### Phase 1 — MVP

- [ ] `gdpm init`
- [ ] `gdpm add`（对接官方 Store API）
- [ ] `gdpm remove`
- [ ] `gdpm list`
- [ ] `gdpm sync`
- [ ] `gdpm.lock` 生成
- [ ] 基础版本解析（精确 + caret `^`）

### Phase 2 — 依赖管理

- [ ] 递归依赖解析
- [ ] `gdpm tree`
- [ ] `gdpm update`
- [ ] `gdpm search`（官方 Store API）
- [ ] `gdpm info`
- [ ] 完整版本约束

### Phase 3 — 高级

- [ ] Git 依赖
- [ ] 本地路径依赖
- [ ] GDExtension 平台感知
- [ ] `gdpm run`
- [ ] `gdpm audit`

### Phase 4 — 生态

- [ ] CI/CD 模板
- [ ] `gdpm doctor`
- [ ] 编辑器插件（GUI）

---

## 13. 竞品对比

| 特性 | gdpm | 官方 Store 编辑器 | 手动安装 |
|------|------|------------------|---------|
| CLI 操作 | ✅ | ❌ | ❌ |
| 依赖解析 | ✅ | ❌ | ❌ |
| 锁文件 | ✅ | ❌ | ❌ |
| CI/CD | ✅ | ❌ | ❌ |
| 平台感知 | ✅ | ❌ | ❌ |
| 编辑器 GUI | ❌（计划中） | ✅ | ❌ |
| 付费插件 | ❌ | ✅（计划中） | ❌ |

---

## 14. 示例工作流

```bash
# 新项目
mkdir my-game && cd my-game
gdpm init my-game --godot 4.3
gdpm add limbo-ai
gdpm add phantom-camera
gdpm add --dev gdunit4
gdpm tree
gdpm run godot -- --editor

# 克隆项目
git clone https://github.com/user/my-game.git
cd my-game
gdpm sync
gdpm run godot -- --editor

# CI
gdpm sync --frozen --no-cache
gdpm run test
```
