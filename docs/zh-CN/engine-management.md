# 引擎管理

GDPM 可以在管理插件的同时管理 Godot 引擎安装。

## 从 GitHub 安装

```bash
# 安装最新的 4.7 稳定版
gdpm godot install 4.7

# 安装指定版本
gdpm godot install 3.6.2-stable

# 安装 C# 版本
gdpm godot install 4.7 --csharp
```

## 添加本地引擎

```bash
# macOS
gdpm godot add /Applications/Godot.app

# Linux
gdpm godot add /usr/local/bin/godot

# 设置别名
gdpm godot add /path/to/Godot --name 4.7-custom
```

## 列出引擎

```bash
# 已安装的引擎
gdpm godot list

# GitHub 上可用的版本
gdpm godot list -r

# 紧凑 ID 视图
gdpm godot list -id
```

## 设置项目引擎

```bash
gdpm godot use gdpm-godot@4.7-stable
```

这会在项目根目录写入 `.engines-conf.json`。

## 设置默认引擎

```bash
# 设置未配置项目的回退引擎
gdpm godot default steam@4.7-stable

# 查看当前默认
gdpm godot default

# 移除默认
gdpm godot default --unset
```

## 打开 Godot

```bash
# 打开编辑器
gdpm godot open

# 运行项目
gdpm godot open --run
```

## 引擎 ID 格式

引擎 ID 使用 `名称@版本` 格式：

- `gdpm-godot@4.7-stable` — 下载的引擎
- `steam@4.7-stable` — 本地引擎（通过 `gdpm godot add` 添加）
