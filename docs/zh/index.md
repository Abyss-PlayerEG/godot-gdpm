# GDPM

Godot 插件的依赖包管理器，类似 uv/npm/cargo。

## 特性

- **一键安装** — `gdpm add limbo-ai`，告别手动下载
- **依赖管理** — 自动依赖解析
- **锁文件** — `gdpm.lock` 确保团队和 CI 安装一致
- **Godot Asset Store** — 直接集成官方商店 API
- **版本约束** — 支持 `^`、`~`、`>=` 语义化版本语法
- **Godot 引擎管理** — 安装、管理和切换 Godot 版本
- **全局缓存** — 跨项目共享缓存，节省磁盘空间

## 快速开始

```bash
pip install godot-gdpm

# 初始化项目
gdpm init

# 添加插件
gdpm add limbo-ai
gdpm add phantom-camera

# git clone 后同步
gdpm sync
```

## 链接

- [GitHub](https://github.com/Abyss-PlayerEG/godot-gdpm)
- [PyPI](https://pypi.org/project/godot-gdpm/)
- [Godot Asset Store](https://store.godotengine.org/)
- [Godot Asset Library](https://godotengine.org/asset-library/)
