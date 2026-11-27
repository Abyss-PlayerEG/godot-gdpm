# 快速入门

## 初始化项目

如果你已有 Godot 项目：

```bash
cd my-godot-project
gdpm init
```

这会在项目目录下创建 `gdproject.toml` 和 `addons/`。

从零开始，在新目录中初始化：

```bash
gdpm init my-game --godot ">=4.2.0"
```

## 添加插件

```bash
gdpm add limbo-ai
gdpm add phantom-camera
gdpm add --dev gdunit4
```

自己写的插件可以不走商店，打包进 `gdpm-local/`：

```bash
gdpm add --local
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

加上 `-y` 可跳过所有确认提示（`gdpm -y sync`）。

## 在 CI 中

```bash
gdpm sync --frozen
```

`--frozen` 严格按锁文件安装，不重新解析版本。
