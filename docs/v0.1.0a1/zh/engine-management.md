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

=== "macOS"

    ```bash
    gdpm godot add /Applications/Godot.app
    ```

=== "Linux"

    ```bash
    gdpm godot add /usr/local/bin/godot
    ```

=== "Windows"

    ```bash
    gdpm godot add "C:\Program Files\Godot\Godot.exe"
    ```

设置别名：

```bash
gdpm godot add /path/to/Godot --name 4.7-custom
```

!!! note
    路径包含空格时需要使用引号，所有平台通用。

## 列出引擎

=== "已安装"

    ```bash
    gdpm godot list
    ```

    ```
    ╭──────────────────── Installed Godot (3) ─────────────────────╮
    │                                                              │
    │   Name               Version              Source             │
    │  ────────────────────────────────────────────────────────    │
    │   gdpm-godot         4.4-stable           ~/.gdpm/engines/   │
    │   gdpm-godot         4.4-stable-csharp    ~/.gdpm/engines/   │
    │   steam-godot        4.7-stable           ~/Library/...      │
    │                                                              │
    ╰──────────────────────────────────────────────────────────────╯
    ```

=== "紧凑 ID"

    ```bash
    gdpm godot list -id
    ```

    ```
    ╭──────────────────── Installed Godot (3) ─────────────────────╮
    │                                                              │
    │   ID                              Source                     │
    │  ────────────────────────────────────────────────────────    │
    │   gdpm-godot@4.4-stable           ~/.gdpm/engines/...        │
    │   gdpm-godot@4.4-stable-csharp    ~/.gdpm/engines/...        │
    │   steam-godot@4.7-stable          ~/Library/...              │
    │                                                              │
    ╰──────────────────────────────────────────────────────────────╯
    ```

=== "远程"

    ```bash
    gdpm godot list -r
    ```

    ```
    ╭────────────── Available Godot Versions (page 1/3) ───────────╮
    │                                                              │
    │   Version                        Type          Date          │
    │  ────────────────────────────────────────────────────────    │
    │   4.7-stable                     Stable        2026-06-18    │
    │   4.6.3-stable                   Stable        2026-05-20    │
    │   4.6.2-stable                   Stable        2026-04-01    │
    │   4.5.2-stable                   Stable        2026-03-19    │
    │   ...                                                        │
    │                                                              │
    ╰──────────────────────────────────────────────────────────────╯
    ```

    额外参数：

    | 参数 | 说明 |
    |------|------|
    | `-V, --version <ver>` | 按版本过滤（如 `4.7`、`3.6`） |
    | `-a, --all` | 显示所有版本，包括 1.x/2.x |
    | `-p, --page <num>` | 分页页码 |

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
