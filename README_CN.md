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
- **Godot 引擎管理** — 安装、管理和切换 Godot 版本
- **全局缓存** — 多项目共享缓存，节省磁盘空间

## 安装

```bash
pip install godot-gdpm
```

## 快速开始

```bash
# 初始化已有项目
gdpm init

# 或创建新项目
gdpm create my-game

# 添加插件
gdpm add limbo-ai
gdpm add phantom-camera

# git clone 后同步
gdpm sync
```

## 文档

- [文档站](https://abyss-playereg.github.io/godot-gdpm/) — 完整文档
- [Godot Asset Store](https://store.godotengine.org/) — 官方插件商店
- [Godot Asset Library](https://godotengine.org/asset-library/) — 社区资源库

## 许可证

GPL-3.0 许可证 — 详见 [LICENSE](LICENSE)
