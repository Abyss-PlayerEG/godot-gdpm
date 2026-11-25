<div align="center">

[![English](https://img.shields.io/badge/English-blue?style=for-the-badge)](README.md) [![简体中文](https://img.shields.io/badge/简体中文-gray?style=for-the-badge)](README_CN.md)

</div>

# gdpm_cf_workers — Self-hosted Godot download CDN (Cloudflare Worker)

Emulates the official download endpoint `downloads.godotengine.org` query
semantics on our own domain `godot-download.playereg.top`, to work around the
302↔504 flapping between this machine and GitHub (caused by accelerators /
local network conditions). **Resolution and origin fetches both go through
GitHub**; the server never probes the official endpoints.

## Architecture

```
gdpm → godot-download.playereg.top/?version=&flavor=&slug=&platform=
        │ Worker (this directory, runs at the CF edge, GitHub-only source)
        ├─ GitHub releases API asset-name matching (platform keywords + mono
        │   filter, cached 1h per tag, dual repo: godot-builds → godot)
        │   → 302 to this domain's /gh/... relay (client only ever hits the CF edge)
        └─ /gh/ relay: CF→GitHub origin fetch (overseas direct, never via local network)
            ├─ full GET → edge cached for 30 days
            └─ Range 206 (gdpm chunked download) → per-chunk origin passthrough
```

- Unauthenticated GitHub API limit is 60/hour (counted per CF egress IP);
  asset resolution is cached 1h per tag, versions assembly is cached 6h.
  For higher volume, configure a token:
  `npx wrangler secret put GITHUB_TOKEN`

## Endpoint parameters

`GET /?version=&flavor=&slug=&platform=` — same semantics as the official
`downloads.godotengine.org`; on the gdpm side it is generated authoritatively
by `_official_asset`:

| Param | Required | Purpose | Accepted values |
|---|---|---|---|
| `version` | ✓ | Version number, joined with flavor to form the tag | `4.7.2` / `4.3` / `3.5.3` (X.Y or X.Y.Z, **no channel suffix**) |
| `flavor` | | Release channel, forms tag `{version}-{flavor}` | `stable` (default) / `rc1` / `beta2` / `dev7` … must match the GitHub release tag suffix **exactly**, otherwise 404 |
| `slug` | ✓ | Asset file-name body; probed directly as `Godot_v{tag}_{slug}` | See table below, **paired with platform** |
| `platform` | | Platform identifier; selects the legacy candidate table and the API keyword branch | See table below, **paired with slug** |

### slug × platform pairing table

| Scenario | `slug` | `platform` |
|---|---|---|
| Windows (all generations) | `win64.exe.zip` | `windows.64` |
| Windows mono | `mono_win64.zip` | `windows.64` |
| macOS ≥ 4.8 (split architectures) | `macos.arm64.zip` / `macos.x86_64.zip` | `macos.arm64` / `macos.x86_64` |
| macOS 4.4–4.7 | `macos.universal.zip` | `macos.universal` |
| macOS < 4 | `osx.universal.zip` | `macos.universal` |
| Linux arm64 | `linux.arm64.zip` | `linux.arm64` |
| Linux x86 ≥ 4 | `linux.x86_64.zip` | `linux.64` |
| Linux x86 < 4 (3.x) | `x11.64.zip` | `linux.64` |
| mono variants | the slugs above with a `mono_` prefix (3.x Linux uses underscores: `mono_x11_64.zip`) | same as above |

When the first slug probe misses, **legacy naming candidates** are expanded
from `platform` and probed in turn (the mono prefix is mirrored onto every
candidate automatically):

- `macos*` → `osx.fat.zip` `osx.64.zip` `osx64.zip` `osx.universal.zip`
- `windows*` → `win64.exe.zip` `win32.exe.zip`
- everything else (linux) → `x11.64.zip` `x11_64.zip` `linux.64.zip` `linux.x86_64.zip`

Still no match → fallback to the GitHub releases API keyword search
(platform keywords + mono filter).

### Responses

| Status | Meaning |
|---|---|
| `302` + `location: .../gh/...` | Resolved; the asset goes through this domain's relay (client never connects to github.com directly) |
| `400` | Missing `version` or `slug` |
| `404` `asset_not_found` | Tag/asset does not exist (including combinations upstream never shipped, e.g. 2.x mono) |
| `405` | Not GET/HEAD |

Note: `slug` and `platform` are **used as a pair** — mixing them selects the
wrong candidate table. The gdpm client only consumes the `stable` channel
(install has a stable-only gate); non-stable values work at the API level only.

## Three-step deploy

```bash
cd src/gdpm_worker_godot_download
npx wrangler login                      # first run: authorize CF account in browser
npx wrangler deploy                     # routes create DNS + certificate automatically
```

Prerequisite: the CF zone for `playereg.top` is under this account (already
true if `gdpm.playereg.top` exists).

## Verification checklist

```bash
BASE="https://godot-download.playereg.top"

# 1. Resolution: any version 302s to this domain's relay (all via GitHub)
curl -sI "$BASE/?version=4.7.2&flavor=stable&slug=macos.universal.zip&platform=macos.universal"
#    → HTTP/2 302, location: .../gh/godotengine/.../Godot_v4.7.2-stable_macos.universal.zip

# 2. Follow the relay to the end: 200 + correct byte count
curl -sIL "$BASE/?version=4.3&flavor=stable&slug=macos.universal.zip&platform=macos.universal" \
  -o /dev/null -w "%{http_code} %{size_download}\n"   # expect 200 (final)

# 3. Legacy asset keyword matching (3.0 → osx.fat)
curl -sI "$BASE/?version=3.0&flavor=stable&slug=osx.universal.zip&platform=macos.universal"
#    → 302 → /gh/godotengine/.../Godot_v3.0-stable_osx.fat.zip

# 4. Range chunks (required by gdpm's chunked download)
curl -s -H "Range: bytes=0-1023" -o /dev/null -w "%{http_code}\n" \
  "$BASE/gh/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_macos.universal.zip"
#    → 206

# 5. Cache-hit check (second request should hit the edge, cf-cache-status: HIT)
curl -sI "<final relay URL from step 2>" | grep -i cf-cache-status
```

## gdpm integration

On the gdpm side **only this mirror is used, with no configuration**: engine
downloads and `versions.json` both go straight to
`godot-download.playereg.top` (the constant `GODOT_DOWNLOAD_MIRROR` is
hard-coded in `src/gdpm/constants.py`); official URLs have been removed from
the client — the query semantics remain word-for-word identical to the
official ones, while GitHub asset matching and relaying are done entirely by
this Worker server-side:

```
gdpm ──> godot-download.playereg.top ──(inside the Worker)──> GitHub (API + relay)
```

To switch mirror domains, change only `GODOT_DOWNLOAD_MIRROR` in
`src/gdpm/constants.py`.

## /versions.json — self-hosted version manifest

Mirrors the official `https://godotengine.org/versions.json` (top-level
`[{name, releases}]` array, groups sorted by descending version, within a
group stable→rc→beta→dev, English display dates). The data source is the
**GitHub releases API**, assembling published versions from two repositories:

- `godot-builds` (357 releases, all 4 pages: includes dev/beta snapshots) +
  the `godot` main repo (fills gaps, includes 1.x/2.x/3.x stable)
- Each page retries once on failure; the assembled result is cached for 6
  hours (decided by the `x-gdpm-built-at` header) and falls back to the
  previous copy when the GitHub API is unavailable; response carries
  `cache-control: public, max-age=3600`
- Differences from the official manifest (expected): only versions that have
  a GitHub tag are included (the official-only 2.0.4 / 2.0.4.1 pairs have no
  GitHub tag and are not covered); versions GitHub has but the official list
  may lack are added (e.g. 3.2.4); `release_notes` points at the GitHub
  release page rather than a godotengine.org article
- On the gdpm side `fetch_remote_versions` also goes only to this mirror's
  `/versions.json` (the single channel)

```bash
curl -s https://godot-download.playereg.top/versions.json | head -c 300
```

## Operations notes

- Free tier: 100k requests/day — a single engine install uses about 40
  requests, so headroom is huge
- **Abuse protection**: `/gh/` only allows `godotengine/<repo>/releases/download/`
  asset paths (no open proxy; SSRF is impossible — the origin host is fixed to
  github.com); GET/HEAD only; no CORS headers (gdpm is a CLI); API 404s for
  non-existent tags are cached 5 minutes (so random versions cannot burn
  quota); probes and assembly results are cached (1h / 6h)
- Residual risk: Range chunk requests are not cacheable, and sustained
  hammering consumes the Worker's daily request quota — if that happens, add
  a Rate Limiting rule in the CF dashboard (1 rule on the free tier)
- `wrangler.toml`'s `[[routes]]` binds a bare hostname (custom_domain); to
  change domains, edit `pattern` and redeploy
- The Worker is a single file `index.js`, no dependencies, no build step
