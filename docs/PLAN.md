# GDPM 开发计划

---

## 架构设计

### 模块依赖图

```
                    ┌─────────────────────────────────────┐
                    │                 CLI                  │
                    │   (click, 命令解析, 用户交互)          │
                    └──────┬──────┬──────┬──────┬─────────┘
                           │      │      │      │
              ┌────────────▼──┐ ┌─▼────┐ ┌▼─────▼──────────┐
              │   installer   │ │config│ │    resolver      │
              │ (下载/安装/卸载)│ │(读写)│ │ (依赖解析)       │
              └───┬───────┬──┘ └──────┘ └───────┬──────────┘
                  │       │                     │
            ┌─────▼──┐ ┌──▼────┐          ┌────▼─────┐
            │  store  │ │ cache │          │  store   │
            │(API客户端)│ │(缓存) │          │ (协议)    │
            └────────┘ └───────┘          └──────────┘
                  │                         │
              ┌───▼────────────────────────▼───┐
              │           models               │
              │  (Plugin, Version, Dependency) │
              └────────────────────────────────┘
                              │
                        ┌─────▼─────┐
                        │  lockfile │
                        │ (锁文件)   │
                        └───────────┘
```

### 模块职责

| 模块 | 职责 | 依赖 | 被依赖 |
|------|------|------|--------|
| `models` | 纯数据结构 | 无 | 所有模块 |
| `config` | 读写配置文件 | models | cli, installer |
| `store` | Store API 客户端 | models, httpx | resolver, installer |
| `cache` | 本地缓存管理 | models | installer |
| `resolver` | 依赖版本求解 | models, store | cli |
| `installer` | 下载/安装/卸载 | models, store, cache | cli |
| `lockfile` | 读写 gdpm.lock | models | cli |
| `cli` | 命令解析 + 交互 | 所有模块 | 用户 |

### 独立性保证

每个模块通过 **Protocol** 定义接口，不直接依赖具体实现：

```python
# store/protocol.py
from typing import Protocol

class StoreProtocol(Protocol):
    async def search(self, query: str) -> list[Plugin]: ...
    async def get_plugin(self, slug: str) -> PluginDetail: ...
    async def get_versions(self, slug: str) -> list[Version]: ...
    async def download(self, slug: str, version: str, dest: Path) -> Path: ...

# cache/protocol.py
class CacheProtocol(Protocol):
    async def get(self, key: str) -> Path | None: ...
    async def put(self, key: str, path: Path) -> None: ...
    async def clean(self) -> None: ...
```

---

## 目录结构

```
src/gdpm/
├── __init__.py              # 版本号
├── __main__.py              # python -m gdpm
│
├── models/                  # 纯数据结构（零依赖）
│   ├── __init__.py
│   ├── plugin.py            # Plugin, PluginDetail
│   ├── version.py           # Version, VersionConstraint
│   ├── dependency.py        # Dependency
│   └── lock.py              # LockEntry, LockFile
│
├── config/                  # 配置读写
│   ├── __init__.py
│   ├── project.py           # gdproject.toml 读写
│   ├── global_config.py     # 全局配置读写
│   └── schema.py            # 配置 Schema 定义
│
├── store/                   # Store API 客户端
│   ├── __init__.py
│   ├── protocol.py          # StoreProtocol
│   ├── client.py            # StoreClient (httpx)
│   └── parser.py            # API 响应解析
│
├── cache/                   # 缓存管理
│   ├── __init__.py
│   ├── protocol.py          # CacheProtocol
│   └── file_cache.py        # FileCache (文件系统实现)
│
├── resolver/                # 依赖解析
│   ├── __init__.py
│   ├── protocol.py          # ResolverProtocol
│   └── solver.py            # DependencySolver (SAT)
│
├── installer/               # 安装/卸载
│   ├── __init__.py
│   ├── protocol.py          # InstallerProtocol
│   └── manager.py           # PluginManager
│
├── lockfile/                # 锁文件
│   ├── __init__.py
│   └── lock.py              # LockFileReader, LockFileWriter
│
├── cli/                     # CLI 命令层
│   ├── __init__.py
│   ├── app.py               # click.Group 入口
│   ├── init.py              # gdpm init
│   ├── add.py               # gdpm add
│   ├── remove.py            # gdpm remove
│   ├── sync.py              # gdpm sync
│   ├── list.py              # gdpm list
│   ├── lock.py              # gdpm lock
│   ├── search.py            # gdpm search
│   ├── info.py              # gdpm info
│   ├── update.py            # gdpm update
│   ├── tree.py              # gdpm tree
│   ├── run.py               # gdpm run
│   ├── config_cmd.py        # gdpm config
│   ├── doctor.py            # gdpm doctor
│   └── common.py            # 共享的 CLI 工具函数
│
└── utils/                   # 通用工具
    ├── __init__.py
    ├── platform.py          # 平台检测
    ├── checksum.py          # SHA256 校验
    └── zip.py               # zip 解压
```

---

## 开发阶段

### Phase 1: 基础骨架（第 1 周）

**目标**：项目能跑起来，CLI 能解析命令

| 任务 | 模块 | 文件 |
|------|------|------|
| 数据模型 | models | `plugin.py`, `version.py`, `dependency.py`, `lock.py` |
| CLI 入口 | cli | `app.py` |
| 配置读写 | config | `project.py`, `global_config.py` |
| `gdpm init` | cli | `init.py` |

**验收**：
```bash
gdpm init my-game --godot 4.3
# 生成 gdproject.toml
```

### Phase 2: Store 对接（第 2 周）

**目标**：能搜索和获取插件信息

| 任务 | 模块 | 文件 |
|------|------|------|
| Store 客户端 | store | `client.py`, `parser.py`, `protocol.py` |
| `gdpm search` | cli | `search.py` |
| `gdpm info` | cli | `info.py` |

**验收**：
```bash
gdpm search "state machine"
gdpm info limbo-ai
```

### Phase 3: 安装核心（第 3 周）

**目标**：能下载和安装插件

| 任务 | 模块 | 文件 |
|------|------|------|
| 缓存管理 | cache | `file_cache.py`, `protocol.py` |
| 安装管理 | installer | `manager.py`, `protocol.py` |
| 工具函数 | utils | `platform.py`, `checksum.py`, `zip.py` |
| `gdpm add` | cli | `add.py` |
| `gdpm remove` | cli | `remove.py` |

**验收**：
```bash
gdpm add limbo-ai
ls addons/limbo-ai/
gdpm remove limbo-ai
```

### Phase 4: 锁文件（第 4 周）

**目标**：可复现安装

| 任务 | 模块 | 文件 |
|------|------|------|
| 锁文件读写 | lockfile | `lock.py` |
| `gdpm lock` | cli | `lock.py` |
| `gdpm sync` | cli | `sync.py` |
| `gdpm list` | cli | `list.py` |

**验收**：
```bash
gdpm add limbo-ai
gdpm remove limbo-ai
gdpm sync    # 恢复 limbo-ai
```

### Phase 5: 依赖解析（第 5-6 周）

**目标**：自动处理子依赖

| 任务 | 模块 | 文件 |
|------|------|------|
| 版本约束解析 | models | `version.py` 扩展 |
| 依赖求解器 | resolver | `solver.py`, `protocol.py` |
| `gdpm update` | cli | `update.py` |
| `gdpm tree` | cli | `tree.py` |

**验收**：
```bash
gdpm add dialogic
gdpm tree
# dialogic v2.0.0
# ├── yatl v1.0.0
# └── filesystem-dock-plus v0.3.0
```

### Phase 6: 完善（第 7-8 周）

**目标**：生产可用

| 任务 | 模块 | 文件 |
|------|------|------|
| `gdpm run` | cli | `run.py` |
| `gdpm config` | cli | `config_cmd.py` |
| `gdpm doctor` | cli | `doctor.py` |
| 错误处理 | 全局 | 统一错误处理 |
| 文档 | - | README, man page |
| 测试 | tests | 各模块单元测试 |

---

## 测试策略

每个模块独立测试：

```
tests/
├── test_models.py         # 纯数据结构测试
├── test_config.py         # 配置读写测试（mock 文件系统）
├── test_store.py          # Store API 测试（mock httpx）
├── test_cache.py          # 缓存测试（临时目录）
├── test_resolver.py       # 依赖解析测试（mock store）
├── test_installer.py      # 安装测试（mock store + cache）
├── test_lockfile.py       # 锁文件测试
└── test_cli.py            # CLI 集成测试（click.testing.CliRunner）
```

测试原则：
- `models` — 纯逻辑测试，无需 mock
- `store` — mock httpx，返回固定 JSON
- `cache` — 使用临时目录
- `resolver` — mock store，提供固定的版本列表
- `installer` — mock store + cache，验证文件操作
- `cli` — 用 CliRunner 测试命令输出

---

## 技术栈

| 组件 | 选型 | 版本 |
|------|------|------|
| Python | >=3.14 | - |
| CLI | click | >=8.1 |
| HTTP | httpx | >=0.27 |
| TOML | tomllib | 标准库 |
| 终端 | rich | >=13.0 |
| 版本 | packaging | >=24.0 |
| 配置路径 | platformdirs | >=4.0 |
| 测试 | pytest | >=8.0 |
| 类型 | mypy | >=1.13 |
| 格式 | ruff | >=0.8 |

---

## 依赖关系矩阵

```
         models  config  store  cache  resolver  installer  lockfile  cli
models     -       ✗       ✗      ✗       ✗         ✗         ✗       ✗
config     ✓       -       ✗      ✗       ✗         ✗         ✗       ✗
store      ✓       ✗       -      ✗       ✗         ✗         ✗       ✗
cache      ✓       ✗       ✗      -       ✗         ✗         ✗       ✗
resolver   ✓       ✗       ✓      ✗       -         ✗         ✗       ✗
installer  ✓       ✗       ✓      ✓       ✗         -         ✗       ✗
lockfile   ✓       ✗       ✗      ✗       ✗         ✗         -       ✗
cli        ✓       ✓       ✓      ✓       ✓         ✓         ✓       -
```

✓ = 依赖（通过 Protocol 接口）  ✗ = 不依赖

**关键约束**：
- `models` 不依赖任何模块
- `cli` 依赖所有模块（组合根）
- 其他模块只依赖 `models` 和通过 Protocol 的可选依赖
