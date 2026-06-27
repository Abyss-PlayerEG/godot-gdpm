<div align="center">

[![English](https://img.shields.io/badge/English-gray?style=for-the-badge)](README.md) [![简体中文](https://img.shields.io/badge/简体中文-blue?style=for-the-badge)](README_CN.md)

</div>

---

# GDPM — Godot 依赖包管理器

> Godot 插件的依赖包管理器，类似 uv/npm/cargo。

[![CI](https://github.com/Abyss-PlayerEG/godot-gdpm/actions/workflows/ci.yml/badge.svg)](https://github.com/Abyss-PlayerEG/godot-gdpm/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/godot-gdpm)](https://pypi.org/project/godot-gdpm/)
[![Python](https://img.shields.io/pypi/pyversions/godot-gdpm)](https://pypi.org/project/godot-gdpm/)
[![License](https://img.shields.io/github/license/Abyss-PlayerEG/godot-gdpm)](LICENSE)

---

## 功能特性

- **一键安装** — `gdpm add limbo-ai` 代替手动下载
- **依赖管理** — 自动解析依赖关系
- **锁文件** — `gdpm.lock` 确保团队和 CI 环境的可复现安装
- **Godot 资产商店** — 直接对接官方商店 API
- **版本约束** — 支持 `^`、`~`、`>=` 语义化版本语法
- **模板检测** — 自动识别项目模板和插件
- **Godot 兼容性** — 检查插件与 Godot 版本的兼容性
- **Godot 引擎管理** — 安装、管理和切换 Godot 版本
- **全局缓存** — 多项目共享缓存，节省磁盘空间
- **Shell 补全** — 支持 zsh、bash、fish 的 Tab 补全

## 安装

```bash
pip install godot-gdpm
```

## 快速开始

```bash
# 初始化项目
gdpm init

# 创建新项目
gdpm create my-game

# 添加插件
gdpm add limbo-ai
gdpm add phantom-camera
gdpm add --dev gdunit4

# 查看状态
gdpm status

# 同步插件（例如 git clone 后）
gdpm sync
```

## 命令

### 项目

| 命令 | 说明 |
|------|------|
| `gdpm init` | 初始化 gdpm 项目 |
| `gdpm create [name]` | 创建新 Godot 项目（交互式） |
| `gdpm sync` | 同步 addons/ 到锁文件状态 |
| `gdpm lock` | 生成或更新锁文件 |
| `gdpm list` | 列出已安装插件 |
| `gdpm status` | 显示插件状态和可用更新 |

### 依赖

| 命令 | 说明 |
|------|------|
| `gdpm add <plugin>` | 添加插件到项目 |
| `gdpm remove <plugin>` | 移除插件 |
| `gdpm update` | 更新插件到新版本 |
| `gdpm search <query>` | 搜索 Godot 资产商店 |
| `gdpm info <plugin>` | 显示插件详情 |

### 引擎管理

| 命令 | 说明 |
|------|------|
| `gdpm godot list` | 列出已安装的 Godot 引擎 |
| `gdpm godot list -r` | 列出 GitHub 上的可用版本 |
| `gdpm godot install <ver>` | 安装 Godot 引擎 |
| `gdpm godot uninstall <ver>` | 卸载 Godot 引擎 |
| `gdpm godot add <path>` | 添加本地 Godot 引擎 |
| `gdpm godot remove <name>` | 移除本地引擎 |
| `gdpm godot use <id>` | 设置项目引擎 |
| `gdpm godot info` | 显示当前引擎信息 |
| `gdpm godot open` | 打开 Godot 编辑器 |
| `gdpm godot default <id>` | 设置默认引擎 |

### 缓存

| 命令 | 说明 |
|------|------|
| `gdpm cache info` | 显示缓存大小和位置 |
| `gdpm cache clean` | 清理所有缓存文件 |

### 导入/导出

| 命令 | 说明 |
|------|------|
| `gdpm export` | 导出插件为 zip 归档 |
| `gdpm import` | 从 zip 归档导入插件 |

## 配置

### gdproject.toml

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

### 版本约束

| 语法 | 含义 | 示例 |
|------|------|------|
| `1.5.0` | 精确版本 | `limbo-ai = "1.5.0"` |
| `^1.5.0` | 兼容更新 | `>=1.5.0, <2.0.0` |
| `~1.5.0` | 补丁更新 | `>=1.5.0, <1.6.0` |
| `>=1.0.0` | 最低版本 | `>=1.0.0` |
| `*` | 任意版本 | `limbo-ai = "*"` |

## 工作原理

gdpm 使用官方 [Godot 资产商店 API](https://store.godotengine.org/api/v1) 来发现和下载插件。**不需要**自定义注册中心。

```
gdpm add limbo-ai
  → 搜索 Godot 资产商店 API
  → 下载插件 zip
  → 解压到 addons/
  → 写入 tag.gdpm 进行追踪
  → 更新 gdproject.toml + gdpm.lock
```

## 引擎管理

gdpm 可以管理 Godot 引擎安装：

```bash
# 安装 Godot 4.7
gdpm godot install 4.7

# 安装 C# 版本
gdpm godot install 4.7 --csharp

# 添加本地引擎（例如 Steam 版本）
gdpm godot add "/path/to/Godot.app"

# 设置当前项目引擎
gdpm godot use gdpm-godot@4.7-stable

# 打开 Godot 编辑器
gdpm godot open
```

## CI/CD 集成

```yaml
# GitHub Actions
- name: Install Godot plugins
  run: |
    pip install godot-gdpm
    gdpm sync --frozen
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/Abyss-PlayerEG/godot-gdpm.git
cd godot-gdpm

# 安装依赖
uv sync

# 运行检查
python scripts/check.py

# 构建可执行文件
python scripts/build.py
```

## 贡献

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feat/new-feature`)
3. 提交更改 (`git commit -m "feat: add new feature"`)
4. 推送到分支 (`git push origin feat/new-feature`)
5. 开启 Pull Request

## 许可证

MIT 许可证 — 详见 [LICENSE](LICENSE)

## 致谢

- [Godot Engine](https://godotengine.org/) — 游戏引擎
- [Godot Asset Store](https://store.godotengine.org/) — 官方插件商店
- [uv](https://github.com/astral-sh/uv) — CLI 设计灵感
- [Rich](https://github.com/Textualize/rich) — 终端格式化
- [Click](https://github.com/pallets/click) — CLI 框架
- [Questionary](https://github.com/tmbo/questionary) — 交互式提示
