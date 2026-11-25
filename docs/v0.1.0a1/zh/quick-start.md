# 快速入门

有两种方式开始使用 GDPM。

## 方式一：初始化已有项目

如果你已有 Godot 项目：

```bash
cd my-godot-project
gdpm init
```

这会在项目目录下创建 `gdproject.toml` 和 `gdpm.lock`。

## 方式二：创建新项目

从零开始，交互式创建：

```bash
gdpm create my-game
```

引导你完成项目名称、Godot 版本、引擎选择，并自动创建项目结构。

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
