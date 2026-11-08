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
| `cli/commands/godot/common.py::build_download_url` | 按 tag 查 release → 资产下载 URL | **`downloads.godotengine.org` 302 接口** |
| `cli/commands/godot/common.py::get_asset_hash` | 资产 SHA256（当前坏的） | **`godot-builds` 的 `files[].checksum`** |
| `cli/commands/godot/list.py`（3 处） | `--remote` 远程版本列表 | **`versions.json`**（静态无速率限制） |
| `cli/app.py:495` `contributors` | `gdpm --about` 展示本仓库贡献者 | **保留 GitHub API**（属 gdpm 自身元数据，非 Godot 下载链） |
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
- mono 支持 ✅；预发布通道已按 stable-only 决策移除（2026-11，list 排除非 stable、install 拒绝非 stable、`-c` 已删）
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

- [x] 新增 `store` 层或 `utils` 模块：`build_download_url(tag, csharp)` 改为官方接口拼接
- [x] 内置 slug 表（按主版本代际 + 平台 + mono 规则，`_official_asset` 显式代际规则）
- [x] 302 由 httpx `follow_redirects=True` 自动跟随（无需显式解析），404 → 友好报错（冒烟 `install 9.9` 验证）
- [x] 保留现有 `download_file_chunked` 下载链不动（拿到直链后照旧）
- [x] 单测：`tests/test_official_download.py` 拼接纯逻辑 11 例（含官网链接逐字断言），404 走冒烟

### Phase 2: 版本列表

- [x] `gdpm godot list --remote` 改读 `versions.json`（新→旧顺序直接展示，通道名即 flavor）
- [x] 评估 `list --remote` 是否还需 GitHub 分页逻辑（已整体删除，改本地分页）

### Phase 3: 校验和（= P0-2 修复）—— 已决策移除

> 2026-11-07 调查结论：**官方无哈希获取接口**，五项探测全部阴性
> （下载接口响应头 / 查询参数 / 官网页面内嵌 / CDN 伴生 403 / tuxfamily 404）。
> 曾实现 godot-builds SHA512 对账并实测通过（`Hash verified ✓`），
> 但唯一哈希源在 GitHub 仓库而非下载接口同源提供，不满足"官方接口"标准，按项目决策整体移除。

- [x] ~~`get_asset_hash` 改查 `godot-builds`~~ → 曾实现为 `get_release_asset`，后按决策移除
- [x] 移除哈希校验分支、`_match_release_file` 与 `sha512_file`
- [x] 下载文件名回归本地构造（官方 slug 规则保留在 `build_download_url`）
- [x] 详见 [质量与安全加固](质量与安全加固.md) P0-2

### Phase 4: 清理与收尾

- [x] `constants.py`：`GODOT_RELEASES_URL` 删除；`GITHUB_API_URL`/token 保留（contributors 用）
- [x] Godot 链路请求全部 `verify=True`（versions.json/下载 CDN/asset-library 实测 certifi 可过）
- [ ] `verify=False` 剩余位置逐个评估（已评估：仅剩 2 处 `api.github.com`——本网络流量被重签、certifi 无法验证，系统信任库可过；`grep = 0` 待网络信任方案后再达）

## 验收

- [ ] `gdpm godot install 4.7` 的**下载 URL 不再走 releases API**（仅 godot-builds 元数据仍走 `api.github.com`，属官方新方案）
- [x] 3.x `x11.64`/`osx.universal` 代际路径由单测逐字断言（本机 macOS 冒烟走 `osx.universal` 分支）
- [x] `gdpm godot list --remote` 连续运行不受速率限制（静态文件）
- [x] hash 校验决策闭环（曾实测 `Hash verified ✓` 生效；经五项探测确认无官方哈希接口后按决策移除，见 Phase 3）
- [x] `python3 scripts/check.py` 全绿 + 新增单测覆盖拼接/解析逻辑（46 例）

## 不在本期范围

- `gdpm --about` 贡献者列表（继续走 GitHub API + token）
- Asset Store API（`store.godotengine.org`，与引擎下载无关）
- Steam 引擎发现/自动解析链（另见引擎解析计划）
