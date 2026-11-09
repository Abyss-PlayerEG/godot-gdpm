# gdpm_cf_workers — 自建 Godot 下载 CDN (Cloudflare Worker)

在自有域名 `godot-download.playereg.top` 上仿真官方下载接口
`downloads.godotengine.org` 的 query 语义, 治理本机到 GitHub 的
302↔504 抖动 (加速器/网络环境所致), 并补齐官方接口对老版本的 slug 缺口.

## 架构

```
gdpm → godot-download.playereg.top/?version=&flavor=&slug=&platform=
        │ Worker (本目录, CF 边缘执行)
        ├─ 探测官方接口 (逐候选 slug, redirect: manual)
        │   ├─ 302 → 对象存储 (≥4.4)      → 直接 302 给客户端 (本机直连可达)
        │   └─ 302 → github.com (≤4.3)    → 302 到本域 /gh/... 中继
        ├─ 官方 404 (1.x/2.x/3.0-mac 未收录)
        │   → GitHub releases API 资产名匹配 (平台关键词 + mono 过滤) → /gh/... 中继
        └─ /gh/ 中继: CF→GitHub 回源 (海外直连, 不经本机网络)
            ├─ 完整 GET → 边缘缓存 30 天
            └─ Range 206 (gdpm 分片) → 逐片回源透传
```

- 服务端 slug 容错: `macos.*` 试 `osx.universal/osx.64/osx64/osx.fat`,
  `linux.64` 试 `x11.64/x11_64/linux.64`, mono 前缀镜像 —— 试中即跳
- GitHub API 未认证限流 60/时 (按 CF 出口 IP 计), 结果缓存 1 小时;
  量大时配 token: `npx wrangler secret put GITHUB_TOKEN`

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

# 1. ≥4.4: 302 直指官方对象存储 (nbg1)
curl -sI "$BASE/?version=4.7.2&flavor=stable&slug=macos.universal.zip&platform=macos.universal"
#    → HTTP/2 302, location: https://godot-releases.nbg1...

# 2. ≤4.3: 302 指向本域中继 (不再直连 github.com)
curl -sI "$BASE/?version=4.3&flavor=stable&slug=macos.universal.zip&platform=macos.universal"
#    → HTTP/2 302, location: .../gh/godotengine/...

# 3. 中继跟到底: 200 + 正确字节数
curl -sIL "$BASE/?version=4.3&flavor=stable&slug=macos.universal.zip&platform=macos.universal" \
  -o /dev/null -w "%{http_code} %{size_download}\n"   # 期望 200 (最终)

# 4. 老版本 slug 缺口 (官方 404 → GitHub 资产匹配兜底)
curl -sI "$BASE/?version=3.0&flavor=stable&slug=osx.universal.zip&platform=macos.universal"
#    → 302 → /gh/godotengine/.../Godot_v3.0-stable_osx.fat.zip

# 5. Range 分片 (gdpm 分片下载依赖)
curl -s -H "Range: bytes=0-1023" -o /dev/null -w "%{http_code}\n" \
  "$BASE/gh/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_macos.universal.zip"
#    → 206

# 6. 缓存命中判定 (二次请求应命中边缘, cf-cache-status: HIT)
curl -sI "<同 3 的最终中继 URL>" | grep -i cf-cache-status
```

## gdpm 接入

gdpm 侧**已写死双通道, 无需任何配置**: 官方接口优先, 走不通 (404 未收录、
本地证书拦截、故障) 自动切换本镜像 —— 官方与镜像的 query 形态逐字一致,
客户端不再直连 GitHub:

```
官方 downloads.godotengine.org ──失败──> 本镜像 godot-download.playereg.top
```

换镜像域名时改两处常量即可: `src/gdpm/constants.py` 的
`GODOT_DOWNLOAD_BASE` / `GODOT_DOWNLOAD_MIRROR`。

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
- gdpm 侧 `fetch_remote_versions` 同样双通道：官方优先，失败自动切本端点

```bash
curl -s https://godot-download.playereg.top/versions.json | head -c 300
```

## 运维备注

- 免费档 10 万请求/天: 单次引擎安装约 40 请求, 余量巨大
- `wrangler.toml` 的 `[[routes]]` 绑定裸主机名 (custom_domain), 换域名改
  `pattern` 重部署即可
- Worker 代码单文件 `index.js`, 无依赖, 无构建步骤
