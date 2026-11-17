# 安装指南

## pip（推荐）

```bash
pip install godot-gdpm
```

预发布版本需要指定版本号：

```bash
pip install godot-gdpm==0.1.0b12
```

## GitHub Releases

从 [Releases](https://github.com/Abyss-PlayerEG/godot-gdpm/releases) 下载。

=== "macOS / Linux"

    ```bash
    tar -xzf gdpm_*_*.tar.gz
    cd gdpm
    ./install.sh
    ```

=== "Windows"

    解压 zip 并运行 `install.bat`。

!!! note "未签名的二进制"
    发布的二进制使用 ad-hoc 签名（无 Apple Developer ID / 未公证）。
    `install.sh` 会自动清除 macOS 隔离属性。如果不使用安装脚本、直接运行二进制：

    ```bash
    xattr -cr gdpm
    ```

    Windows 上首次运行会弹出 SmartScreen 警告——选择"更多信息" → "仍要运行"。

## 验证

```bash
gdpm -V
```
