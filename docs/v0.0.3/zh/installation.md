# 安装指南

## pip（推荐）

```bash
pip install godot-gdpm
```

## GitHub Releases

从 [Releases](https://github.com/Abyss-PlayerEG/godot-gdpm/releases) 下载。

=== "macOS / Linux"

    ```bash
    tar -xzf gdpm_*_*.tar.gz
    sudo mv gdpm /usr/local/bin/
    ```

=== "Windows"

    解压 zip，将包含 `gdpm.exe` 的目录加入 `PATH`。

!!! note "未签名的二进制"
    发布的二进制使用 ad-hoc 签名（无 Apple Developer ID / 未公证）。
    macOS 上运行前需先清除隔离属性：

    ```bash
    xattr -cr gdpm
    ```

    Windows 上首次运行会弹出 SmartScreen 警告——选择"更多信息" → "仍要运行"。

## 验证

```bash
gdpm -V
```
