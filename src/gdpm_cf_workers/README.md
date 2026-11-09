# gdpm_cf_workers — 自建 Godot 下载 CDN (Cloudflare Worker)

在自有域名 `godot-download.playereg.top` 上仿真官方下载接口
`downloads.godotengine.org` 的 query 语义, 治理本机到 GitHub 的
302↔504 抖动 (加速器/网络环境所致); **解析与回源全部经 GitHub**,
服务端不探测官方接口.

## 架构

```
gdpm → godot-download.playereg.top/?version=&flavor=&slug=&platform=
        │ Worker (本目录, CF 边缘执行, 纯 GitHub 源)
        ├─ GitHub releases API 资产名匹配 (平台关键词 + mono 过滤,
        │   按 tag 缓存 1 小时, godot-builds → godot 双仓库)
        │   → 302 到本域 /gh/... 中继 (客户端只走 CF 边缘)
        └─ /gh/ 中继: CF→GitHub 回源 (海外直连, 不经本机网络)
            ├─ 完整 GET → 边缘缓存 30 天
            └─ Range 206 (gdpm 分片) → 逐片回源透传
```

- GitHub API 未认证限流 60/时 (按 CF 出口 IP 计), 资产解析按 tag 缓存
  1 小时、versions 组装缓存 6 小时; 量大时配 token:
  `npx wrangler secret put GITHUB_TOKEN`

## 接口参数

`GET /?version=&flavor=&slug=&platform=` —— 与官方
`downloads.godotengine.org` 同语义, gdpm 侧由 `_official_asset` 权威生成:

| 参数 | 必填 | 作用 | 可填值 |
|---|---|---|---|
| `version` | ✓ | 版本号, 与 flavor 拼成 tag | `4.7.2` / `4.3` / `3.5.3` (X.Y 或 X.Y.Z, **不带通道**) |
| `flavor` | | 发布通道, 拼成 tag `{version}-{flavor}` | `stable` (默认) / `rc1` / `beta2` / `dev7` … 必须与 GitHub release tag 后缀**逐字一致**, 否则 404 |
| `slug` | ✓ | 资产文件名主体, 直构 `Godot_v{tag}_{slug}` 试探 | 见下表, **与 platform 成对** |
| `platform` | | 平台标识, 决定历史候选表与 API 关键词分支 | 见下表, **与 slug 成对** |

### slug × platform 成对取值表

| 场景 | `slug` | `platform` |
|---|---|---|
| Windows (全代际) | `win64.exe.zip` | `windows.64` |
| Windows mono | `mono_win64.zip` | `windows.64` |
| macOS ≥ 4.8 (架构拆分) | `macos.arm64.zip` / `macos.x86_64.zip` | `macos.arm64` / `macos.x86_64` |
| macOS 4.4–4.7 | `macos.universal.zip` | `macos.universal` |
| macOS < 4 | `osx.universal.zip` | `macos.universal` |
| Linux arm64 | `linux.arm64.zip` | `linux.arm64` |
| Linux x86 ≥ 4 | `linux.x86_64.zip` | `linux.64` |
| Linux x86 < 4 (3.x) | `x11.64.zip` | `linux.64` |
| mono 变体 | 上述 slug 加 `mono_` 前缀 (3.x linux 为 `mono_x11_64.zip` 下划线) | 同上 |

slug 首试未命中时, 按 `platform` 展开**历史命名候选**继续试探 (mono 前缀
自动镜像到每个候选):

- `macos*` → `osx.fat.zip` `osx.64.zip` `osx64.zip` `osx.universal.zip`
- `windows*` → `win64.exe.zip` `win32.exe.zip`
- 其余 (linux) → `x11.64.zip` `x11_64.zip` `linux.64.zip` `linux.x86_64.zip`

再未命中 → GitHub releases API 关键词兜底 (平台关键词 + mono 过滤).

### 响应

| 状态 | 含义 |
|---|---|
| `302` + `location: .../gh/...` | 解析成功, 资产走本域中继 (客户端不直连 github.com) |
| `400` | 缺 `version` 或 `slug` |
| `404` `asset_not_found` | tag/资产不存在 (含上游本就没有的组合, 如 2.x mono) |
| `405` | 非 GET/HEAD |

注意: `slug` 与 `platform` **成对使用**, 交叉填写会导向错误的候选表;
gdpm 客户端只消费 stable 通道 (install 有 stable-only 门禁), 非 stable
值仅接口层面可用。

## 部署三步

```bash
cd src/gdpm_cf_workers
npx wrangler login                      # 首次: 浏览器授权 CF 账号
npx wrangler deploy                     # routes 自动创建 DNS + 证书
```

前提: `playereg.top` 的 CF zone 在本账号下 (已有 `gdpm.playereg.top` 则满足).

## 验证清单

```bash
BASE="https://godot-download.playereg.top"

# 1. 解析: 任意版本 302 到本域中继 (全部经 GitHub)
curl -sI "$BASE/?version=4.7.2&flavor=stable&slug=macos.universal.zip&platform=macos.universal"
#    → HTTP/2 302, location: .../gh/godotengine/.../Godot_v4.7.2-stable_macos.universal.zip

# 2. 中继跟到底: 200 + 正确字节数
curl -sIL "$BASE/?version=4.3&flavor=stable&slug=macos.universal.zip&platform=macos.universal" \
  -o /dev/null -w "%{http_code} %{size_download}\n"   # 期望 200 (最终)

# 3. 老版本资产关键词匹配 (3.0 → osx.fat)
curl -sI "$BASE/?version=3.0&flavor=stable&slug=osx.universal.zip&platform=macos.universal"
#    → 302 → /gh/godotengine/.../Godot_v3.0-stable_osx.fat.zip

# 4. Range 分片 (gdpm 分片下载依赖)
curl -s -H "Range: bytes=0-1023" -o /dev/null -w "%{http_code}\n" \
  "$BASE/gh/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_macos.universal.zip"
#    → 206

# 5. 缓存命中判定 (二次请求应命中边缘, cf-cache-status: HIT)
curl -sI "<同 2 的最终中继 URL>" | grep -i cf-cache-status
```

## gdpm 接入

gdpm 侧**只走本镜像, 无任何配置**: 引擎下载与 `versions.json` 均直打
`godot-download.playereg.top` (常量 `GODOT_DOWNLOAD_MIRROR` 写死在
`src/gdpm/constants.py`), 官方 URL 已从客户端移除 —— query 语义仍与官方
逐字一致, GitHub 资产匹配与中继全部由本 Worker 服务端完成:

```
gdpm ──> godot-download.playereg.top ──(Worker 内部)──> GitHub (API + 中继)
```

换镜像域名时只改 `src/gdpm/constants.py` 的 `GODOT_DOWNLOAD_MIRROR` 一处。

## /versions.json — 自建版本清单

仿官方 `https://godotengine.org/versions.json`（顶层 `[{name, releases}]` 数组、
组间版本号倒序、组内 stable→rc→beta→dev、英文展示日期），数据源为
**GitHub releases API** 整理两个仓库的已发布版本：

- `godot-builds`（357 个 release，4 页全量：含 dev/beta 快照）+ `godot` 主仓库（补缺，含 1.x/2.x/3.x stable）
- 单页失败自动重试 1 次；组装结果缓存 6 小时（`x-gdpm-built-at` 头判定），
  GitHub API 不可用时回退上一份；响应 `cache-control: public, max-age=3600`
- 与官方差异（预期内）：仅含 GitHub 有 tag 的版本（官方独有的 2.0.4/2.0.4.1
  两组无 GitHub tag，不覆盖）；官方可能缺而 GitHub 有的会补上（如 3.2.4）；
  `release_notes` 指向 GitHub release 页而非 godotengine.org 文章
- gdpm 侧 `fetch_remote_versions` 也只走本镜像 `/versions.json`（唯一通道）

```bash
curl -s https://godot-download.playereg.top/versions.json | head -c 300
```

## 运维备注

- 免费档 10 万请求/天: 单次引擎安装约 40 请求, 余量巨大
- **滥用防护**: `/gh/` 仅放行 `godotengine/<repo>/releases/download/` 资产
  路径 (防开放代理, SSRF 不可能 —— 回源主机固定 github.com); 仅 GET/HEAD;
  无 CORS 头 (gdpm 为 CLI); 不存在 tag 的 API 404 短缓存 5 分钟 (防随机
  版本消耗配额); 试探/组装结果均有缓存 (1h/6h)
- 残余风险: Range 分片请求不可缓存, 持续轰击会消耗 Worker 日请求配额 ——
  若发生可在 CF 面板加 Rate Limiting 规则 (免费档 1 条)
- `wrangler.toml` 的 `[[routes]]` 绑定裸主机名 (custom_domain), 换域名改
  `pattern` 重部署即可
- Worker 代码单文件 `index.js`, 无依赖, 无构建步骤
