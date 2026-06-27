# 快速入门

## 初始化项目

```bash
cd my-godot-project
gdpm init
```

这会创建 `gdproject.toml` 和 `gdpm.lock`。

## 创建新项目

```bash
gdpm create my-game
```

交互式引导你完成项目设置、Godot 版本和引擎选择。

## 添加插件

```bash
gdpm add limbo-ai
gdpm add phantom-camera
gdpm add --dev gdunit4
```

## 查看状态

```bash
gdpm status
```

## git clone 后同步

```bash
gdpm sync
```

从 `gdpm.lock` 安装所有插件——确保团队成员安装一致。
