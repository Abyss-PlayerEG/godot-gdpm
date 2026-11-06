# GitHub API → 官方 API 迁移

> 来源：2026-11 官方下载接口调研（`versions.json` / `downloads.godotengine.org` / `godot-builds` 三源已实测验证）。
> 目标：Godot 引擎相关请求全部改走官方接口，摆脱 GitHub API 速率限制与关键词猜测。
> 与 [质量与安全加固](质量与安全加固.md) P0-1/P0-2 联动实施。

## 背景：现状问题

| 问题 | 说明 |
|------|------|
| 速率限制 | GitHub API 未认证 60 次/小时，`list --remote` 多查几次即触顶（token 方案只是缓解） |
| 关键词歧义 | `build_download_url` 靠资产名关键词猜平台：3.x Linux `x11.64` 失配、`linux` 不分架构、win32/win64 抢匹配 |
| 校验失效 | `get_asset_hash` 请求错误端点（`contributors`），恒返回空，见 P0-2 |
| TLS 裸奔 | 全部 GitHub 请求 `verify=False`，见 P0-1 |

## 现状盘点：GitHub API 使用点

| 位置 | 用途 | 迁移目标 |
|------|------|---------|
| `cli/godot/common.py::build_download_url` | 按 tag 查 release → 资产下载 URL | **`downloads.godotengine.org` 302 接口** |
| `cli/godot/common.py::get_asset_hash` | 资产 SHA256（当前坏的） | **`godot-builds` 的 `files[].checksum`** |
| `cli/godot/list.py`（3 处） | `--remote` 远程版本列表 | **`versions.json`**（静态无速率限制） |
| `cli/app.py:495` `contributors` | `gdpm --info` 展示本仓库贡献者 | **保留 GitHub API**（属 gdpm 自身元数据，非 Godot 下载链） |
| `constants.py` token/headers | GitHub 认证头 | 保留（contributors 仍用；Godot 链路不再需要） |

## 目标：官方三件套

```
① https://godotengine.org/versions.json
   版本列表: 76 组 366 版 (1.0~4.8, 含 stable/rc/beta/dev), 静态文件无速率限制
   结构: [{name: "4.8", releases: [{name: "beta2", release_date, release_notes}]}]

② https://downloads.godotengine.org/?version=&flavor=&slug=&platform=
   下载 URL 解析: 302 → 官方 CDN (godot-releases.nbg1.your-objectstorage.com)
                 或 GitHub godot-builds (3.x 老版本)
   404 = 版本/组合不存在, 失败语义干净

③ github.com/godotengine/godot-builds/releases/godot-{tag}.json
   权威元数据: files[].filename + checksum, 用于校验与文件名对正
```

实测记录（2026-11-07）：
- `4.8-beta2` / `4.7.2-stable` → 302 到官方 CDN ✅
- `3.6-stable` → 302 到 GitHub godot-builds ✅
- mono / 预发布通道均支持 ✅
- httpx 默认校验（certifi）访问官方接口成功 → P0-1 关闭 `verify=False` 无兼容障碍

## 平台参数表（内置 slug 表，唯一需维护的资产）

| 平台 | 3.x slug | 4.0~4.7 slug | 4.8+ slug | platform（恒定） |
|------|----------|--------------|-----------|------------------|
| Linux x64 | `x11.64.zip` | `linux.x86_64.zip` | `linux.x86_64.zip` | `linux.64` |
| Linux arm64 | — | `linux.arm64.zip` | `linux.arm64.zip` | `linux.arm64` |
| Windows x64 | `win64.exe.zip` | `win64.exe.zip` | `win64.exe.zip` | `windows.64` |
| Windows x86 | `win32.exe.zip` | `win32.exe.zip` | `win32.exe.zip` | `windows.32` |
| macOS | `osx.universal.zip` | `macos.universal.zip` | `macos.arm64.zip`（拆分架构） | `macos.arm64` / `macos.universal` |

mono 规则：slug 加 `mono_` 前缀并去 `.exe`（`win64.exe.zip` → `mono_win64.zip`），platform 不变。

**坑位记录**：
- `platform` 是分组不是架构名（`linux.64` ≠ `linux.x86_64`）
- slug 必填，省略或传完整文件名都是 404（实测）
- 4.8 起 macOS 拆分 arm64/x86_64，slug 表按代际分档，新大版本发布时对照官网 archive 页核对

## 实施分期

### Phase 1: 下载 URL 解析（核心收益）

- [ ] 新增 `store` 层或 `utils` 模块：`build_download_url(tag, csharp)` 改为官方接口拼接
- [ ] 内置 slug 表（按主版本代际 + 平台 + mono 规则，约 10 行）
- [ ] 302 解析：`httpx.head(follow_redirects=False)` 取 `Location`，404 → 友好报错
- [ ] 保留现有 `download_file_chunked` 下载链不动（拿到直链后照旧）
- [ ] 单测：拼接函数纯逻辑测试 + 本地 mock 302/404

### Phase 2: 版本列表

- [ ] `gdpm godot list --remote` 改读 `versions.json`（新→旧顺序直接展示，通道名即 flavor）
- [ ] 评估 `list --remote` 是否还需 GitHub 分页逻辑（预计整体删除）

### Phase 3: 校验和（= P0-2 修复）

- [ ] `get_asset_hash` 改查 `godot-builds`：`releases/godot-{tag}.json` → 按 `files[].filename` 匹配取 `checksum`
- [ ] 文件名来源同样取 `files[].filename`，顺带修复 csharp 资产名不匹配（`-csharp` vs `_mono`）
- [ ] 校验失败中止安装（现有清理逻辑已就绪）
- [ ] 详见 [质量与安全加固](质量与安全加固.md) P0-2

### Phase 4: 清理与收尾

- [ ] `constants.py`：`GODOT_RELEASES_URL` 删除；`GITHUB_API_URL`/token 保留（contributors 用）
- [ ] Godot 链路请求全部 `verify=True`（P0-1 范围，官方接口 certifi 实测可过）
- [ ] `verify=False` 剩余位置逐个评估，目标 `grep -rn "verify=False" src/` = 0

## 验收

- [ ] `gdpm godot install 4.7` 全程不触 `api.github.com`
- [ ] `gdpm godot install 3.6`（3.x Linux `x11.64` 路径）成功——当前关键词方案必挂的用例
- [ ] `gdpm godot list --remote` 连续运行不受速率限制
- [ ] hash 校验真实生效（篡改 zip 必须失败，P0-2 验收）
- [ ] `python3 scripts/check.py` 全绿 + 新增单测覆盖拼接/解析逻辑

## 不在本期范围

- `gdpm --info` 贡献者列表（继续走 GitHub API + token）
- Asset Store API（`store.godotengine.org`，与引擎下载无关）
- Steam 引擎发现/自动解析链（另见引擎解析计划）
