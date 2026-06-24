# Godot 引擎版本管理

## 目标

管理每个项目使用的 Godot 版本，类似 pyenv 管理 Python 版本。

## 命令设计

```bash
gdpm godot install 4.3    # 安装 Godot 4.3
gdpm godot use 4.3        # 设置项目版本
gdpm godot list           # 列出已安装版本
gdpm godot run -- --editor # 运行项目 Godot
```

## 存储结构

```
~/.gdpm/
├── engines/
│   ├── 4.3.0/
│   │   └── Godot_v4.3-stable_macos.universal
│   ├── 4.7.0/
│   │   └── Godot_v4.7-stable_macos.universal
│   └── 4.7.0-rc1/
│       └── Godot_v4.7-rc1_macos.universal
└── config.toml

项目/
├── gdproject.toml
├── gdpm.lock
└── .gdpm-godot            # 4.3.0
```

## 实现步骤

### gdpm godot install

- [ ] 下载 Godot 官方二进制（GitHub Releases）
- [ ] 存储到 ~/.gdpm/engines/{version}/
- [ ] 支持平台检测（macOS/Linux/Windows）
- [ ] 支持 Godot 3.x 和 4.x
- [ ] 支持 --pre（预发布版本）

### gdpm godot use

- [ ] 设置项目使用的 Godot 版本
- [ ] 写入 .gdpm-godot 文件
- [ ] 自动检测 project.godot 兼容性
- [ ] 版本约束匹配（">=4.2"）

### gdpm godot list

- [ ] 列出已安装的 Godot 版本
- [ ] 标记当前项目使用的版本
- [ ] 显示最新可用版本

### gdpm godot run

- [ ] 运行项目对应的 Godot 版本
- [ ] 传递参数给 Godot（如 --editor）
- [ ] 支持 gdproject.toml 中的 scripts
- [ ] 自动下载缺失版本（可选）

## 下载源

```
https://github.com/godotengine/godot/releases/download/{tag}/Godot_v{version}_{platform}.{ext}

示例:
https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_macos.universal.zip
https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_linux.x86_64.zip
https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_win64.exe.zip
```

## 平台检测

macOS:
- `/Applications/Godot.app/Contents/MacOS/Godot`
- Steam: `~/Library/Application Support/Steam/steamapps/common/Godot Engine/Godot.app/Contents/MacOS/Godot`

Linux:
- `which godot`
- `/usr/local/bin/godot`

Windows:
- `where godot.exe`
- `%LOCALAPPDATA%\Godot\`
