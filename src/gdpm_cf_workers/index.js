/**
 * godot-download — Godot 下载接口仿真 Cloudflare Worker (纯 GitHub 源)
 *
 * 仿 downloads.godotengine.org 的 query 语义:
 *   /?version=4.7.2&flavor=stable&slug=macos.universal.zip&platform=macos.universal
 *
 * 解析链路 (不探测官方接口, 全部经 GitHub):
 *   1. /?query → 直构资产名经 github.com HEAD 试探 (零 API 配额) → 302 本域
 *      中继; 未命中再走 GitHub releases API 资产匹配 (平台关键词 + mono
 *      过滤, 按 tag 缓存 1 小时, 覆盖老版本命名差异)
 *   2. /gh/ 中继: CF → GitHub 回源 (海外直连, 不经本机网络), 完整 GET 边缘
 *      缓存 30 天, Range 分片透传 (206 不缓存, 逐片回源, CF→GitHub 稳定)
 *   3. /versions.json: 仿官方 godotengine.org/versions.json, 经 GitHub
 *      releases API 整理两仓库已发布版本 (含 dev/beta 快照), schema 一致;
 *      组装结果缓存 6 小时, GitHub API 不可用时回退上一份
 *
 * 部署与验证见同目录 README.md.
 */

const REPOS = ["godotengine/godot-builds", "godotengine/godot"];
const API_CACHE_TTL = 3600;
const ASSET_CACHE_TTL = 30 * 24 * 3600;
const VERSIONS_TTL = 6 * 3600;
const VERSIONS_BUILT_AT = "x-gdpm-built-at";
const RELEASE_PAGES_CAP = 8;
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return json(405, { error: "method_not_allowed" });
      }
      return resolveAsset(url, env, ctx);
    }

    if (url.pathname.startsWith("/gh/godotengine/")) {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return json(405, { error: "method_not_allowed" });
      }
      return relayGitHub(request, url, ctx);
    }

    if (url.pathname === "/versions.json") {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return json(405, { error: "method_not_allowed" });
      }
      return versionsJson(request, env, ctx);
    }

    if (
      url.pathname === "/debug-probe" ||
      url.pathname === "/debug-api" ||
      url.pathname === "/debug-resolve"
    ) {
      return debugProbe(url, env);
    }

    return json(404, { error: "not_found" });
  },
};

async function resolveAsset(url, env, ctx) {
  const version = url.searchParams.get("version");
  const flavor = url.searchParams.get("flavor") || "stable";
  const slug = url.searchParams.get("slug");
  const platform = url.searchParams.get("platform") || "";
  if (!version || !slug) {
    return json(400, { error: "bad_request", need: ["version", "slug"] });
  }

  // 纯 GitHub 源: releases API 资产名匹配 → 302 到本域中继
  const ghUrl = await resolveFromGitHub(version, flavor, slug, platform, env, ctx);
  if (!ghUrl) {
    return json(404, {
      error: "asset_not_found",
      version,
      flavor,
      slug,
      platform,
    });
  }
  const target = new URL(ghUrl);
  if (target.hostname !== "github.com") {
    // 非 github.com 直链 (异常情况): 原样透传
    return Response.redirect(target.toString(), 302);
  }
  // github 直链改走本域中继, 客户端不再直连 github.com
  return Response.redirect(
    `${url.origin}/gh${target.pathname}${target.search}`,
    302
  );
}

async function resolveFromGitHub(version, flavor, slug, platform, env, ctx) {
  const tag = `${version}-${flavor}`;

  // 1) 零 API 直构: Godot_v{tag}_{候选名} 覆盖常规与历史命名 (3.0 的 osx.fat
  //    等), 经 github.com 直链 HEAD 试探 (302=存在), 不占 API 限流配额;
  //    试探结果按 tag 缓存 1 小时
  for (const name of assetNames(slug, platform)) {
    const assetFile = `Godot_v${tag}_${name}`;
    for (const repo of REPOS) {
      if (await assetExists(repo, tag, assetFile)) {
        return `https://github.com/${repo}/releases/download/${tag}/${assetFile}`;
      }
    }
  }

  // 2) API 兜底: 直构覆盖不了的异形命名 (1.x 的 v1.1_stable 下划线等)
  const mono = slug.startsWith("mono_");
  const keywords = platformKeywords(platform);

  for (const repo of REPOS) {
    const release = await fetchRelease(repo, tag, env, ctx);
    if (!release) continue;
    for (const asset of release.assets || []) {
      const name = asset.name;
      if (name.includes("server")) continue;
      if (mono !== name.includes("_mono")) continue;
      if (name.endsWith(".zip") && keywords.some((k) => name.includes(k))) {
        return asset.browser_download_url;
      }
    }
  }
  return null;
}

/**
 * 直构资产名候选: 请求 slug 首试, 再按平台试历史命名变体
 * (3.0/3.1/3.2 的 osx.*、3.x 的 x11、1.x/2.x 的 win32 等), mono 前缀镜像.
 */
function assetNames(slug, platform) {
  const mono = slug.startsWith("mono_");
  const base = mono ? slug.slice(5) : slug;

  let alts;
  if (platform.startsWith("macos")) {
    alts = ["osx.fat.zip", "osx.64.zip", "osx64.zip", "osx.universal.zip"];
  } else if (platform.startsWith("windows")) {
    alts = ["win64.exe.zip", "win32.exe.zip"];
  } else {
    alts = ["x11.64.zip", "x11_64.zip", "linux.64.zip", "linux.x86_64.zip"];
  }

  const out = [slug];
  for (const alt of alts) {
    if (alt === base) continue;
    const candidate = mono ? `mono_${alt}` : alt;
    if (!out.includes(candidate)) out.push(candidate);
  }
  return out;
}

async function assetExists(repo, tag, name) {
  // github.com 资产直链 HEAD: 302 (存在) / 404 (不存在), CDN 直链不限流;
  // 结果缓存 1 小时 (资产名随 tag 不可变), 网络失败不缓存
  const cacheKey = new Request(
    `https://gdpm-worker-cache/exists-v2/${repo}/${tag}/${name}`
  );
  const hit = await caches.default.match(cacheKey);
  if (hit) return (await hit.text()) === "1";

  let exists = false;
  try {
    const resp = await fetch(
      `https://github.com/${repo}/releases/download/${tag}/${encodeURIComponent(name)}`,
      { method: "HEAD", redirect: "manual" }
    );
    if (resp.status >= 300 && resp.status < 400) {
      exists = true;
    } else if (resp.status !== 404) {
      // 非确定性状态 (5xx 等): 不缓存, 交由下一候选/仓库
      return false;
    }
  } catch {
    return false;
  }

  const store = caches.default.put(
    cacheKey,
    new Response(exists ? "1" : "0", {
      headers: { "cache-control": "public, max-age=3600" },
    })
  );
  await store;
  return exists;
}

function platformKeywords(platform) {
  if (platform.startsWith("macos")) return ["osx", "macos"];
  if (platform.startsWith("linux")) return ["linux", "x11"];
  return ["win"];
}

async function fetchRelease(repo, tag, env, ctx) {
  const cacheKey = new Request(
    `https://gdpm-worker-cache/${repo}/releases/tags/${tag}`
  );
  const hit = await caches.default.match(cacheKey);
  if (hit) return hit.json();

  const headers = {
    accept: "application/vnd.github+json",
    "user-agent": "godot-download-worker",
  };
  if (env.GITHUB_TOKEN) {
    headers.authorization = `Bearer ${env.GITHUB_TOKEN}`;
  }

  let resp;
  try {
    resp = await fetch(
      `https://api.github.com/repos/${repo}/releases/tags/${encodeURIComponent(tag)}`,
      { headers }
    );
  } catch {
    return null;
  }
  // 404/限流不缓存 (限流 403 若入缓存会中毒 1 小时)
  if (!resp.ok) return null;

  const text = await resp.text();
  ctx.waitUntil(
    caches.default.put(
      cacheKey,
      new Response(text, {
        headers: {
          "content-type": "application/json; charset=utf-8",
          "cache-control": `public, max-age=${API_CACHE_TTL}`,
        },
      })
    )
  );
  return JSON.parse(text);
}

async function relayGitHub(request, url, ctx) {
  const range = request.headers.get("range");
  const full = request.method === "GET" && !range;
  const cacheKey = new Request(url.toString(), { method: "GET" });

  if (full) {
    const hit = await caches.default.match(cacheKey);
    if (hit) return withRelayHeaders(hit);
  }

  const origin = `https://github.com${url.pathname.slice(3)}`;
  const headers = { "accept-encoding": "identity" };
  if (range) headers.range = range;

  let resp;
  try {
    resp = await fetch(origin, {
      method: request.method,
      redirect: "follow",
      headers,
    });
  } catch (error) {
    return json(502, { error: "upstream_failed", detail: String(error) });
  }

  if (full && resp.ok && !resp.headers.get("set-cookie")) {
    // 资产不可变, 完整 GET 缓存 30 天; Range 206 走逐片回源不入缓存
    ctx.waitUntil(caches.default.put(cacheKey, resp.clone()));
  }

  const out = new Response(request.method === "HEAD" ? null : resp.body, resp);
  return withRelayHeaders(out);
}

function withRelayHeaders(resp) {
  const out = new Response(resp.body, resp);
  out.headers.set("cache-control", `public, max-age=${ASSET_CACHE_TTL}`);
  out.headers.set("access-control-allow-origin", "*");
  return out;
}

function json(status, body) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

/* ---------- 诊断端点 (运维用): CF 出口到 github 的真实状态 ---------- */

async function debugProbe(url, env) {
  if (url.pathname === "/debug-resolve") {
    // 逐跳追踪解析全过程 (绕过一切缓存), 定位 asset_not_found 的确切环节
    const version = url.searchParams.get("version");
    const flavor = url.searchParams.get("flavor") || "stable";
    const slug = url.searchParams.get("slug");
    const platform = url.searchParams.get("platform") || "";
    const tag = `${version}-${flavor}`;
    const probes = [];
    for (const name of assetNames(slug, platform)) {
      for (const repo of REPOS) {
        const probeUrl = `https://github.com/${repo}/releases/download/${tag}/${encodeURIComponent(name)}`;
        const t0 = Date.now();
        try {
          const resp = await fetch(probeUrl, {
            method: "HEAD",
            redirect: "manual",
          });
          probes.push({ repo, name, status: resp.status, ms: Date.now() - t0 });
        } catch (error) {
          probes.push({ repo, name, error: String(error), ms: Date.now() - t0 });
        }
      }
    }
    const api = [];
    for (const repo of REPOS) {
      const t0 = Date.now();
      try {
        const resp = await fetch(
          `https://api.github.com/repos/${repo}/releases/tags/${tag}`,
          {
            headers: {
              accept: "application/vnd.github+json",
              "user-agent": "godot-download-worker",
              ...(env.GITHUB_TOKEN
                ? { authorization: `Bearer ${env.GITHUB_TOKEN}` }
                : {}),
            },
          }
        );
        api.push({ repo, status: resp.status, ms: Date.now() - t0 });
      } catch (error) {
        api.push({ repo, error: String(error), ms: Date.now() - t0 });
      }
    }
    return json(200, { tag, slug, probes, api });
  }

  if (url.pathname === "/debug-api") {
    // CF 出口调 GitHub API 限流余量 (只允许该固定端点, 防开放代理)
    const t0 = Date.now();
    try {
      const resp = await fetch("https://api.github.com/rate_limit", {
        headers: {
          accept: "application/vnd.github+json",
          "user-agent": "godot-download-worker",
          ...(env.GITHUB_TOKEN
            ? { authorization: `Bearer ${env.GITHUB_TOKEN}` }
            : {}),
        },
      });
      const body = await resp.json();
      return json(200, {
        status: resp.status,
        ms: Date.now() - t0,
        core: body?.resources?.core,
      });
    } catch (error) {
      return json(200, { error: String(error), ms: Date.now() - t0 });
    }
  }

  // HEAD 指定 github.com 直链, 返回原始状态码与耗时
  const target = url.searchParams.get("target") || "";
  if (!target.startsWith("https://github.com/")) {
    return json(400, { error: "target must be https://github.com/..." });
  }
  const t0 = Date.now();
  try {
    const resp = await fetch(target, { method: "HEAD", redirect: "manual" });
    return json(200, {
      status: resp.status,
      location: (resp.headers.get("location") || "").slice(0, 120),
      ms: Date.now() - t0,
    });
  } catch (error) {
    return json(200, { error: String(error), ms: Date.now() - t0 });
  }
}

/* ---------- /versions.json: 仿官方 schema, 源为 GitHub releases ---------- */

async function versionsJson(request, env, ctx) {
  const cacheKey = new Request("https://gdpm-worker-cache/versions.json");
  const hit = await caches.default.match(cacheKey);
  const builtAt = hit ? Number(hit.headers.get(VERSIONS_BUILT_AT) || 0) : 0;

  if (hit && builtAt && Date.now() - builtAt < VERSIONS_TTL * 1000) {
    return versionsResponse(request, hit.body, hit.headers);
  }

  let body;
  try {
    body = JSON.stringify(await assembleVersions(env));
  } catch (error) {
    // GitHub API 不可用: 回退上一份组装结果 (即使已过重建周期)
    if (hit) return versionsResponse(request, hit.body, hit.headers);
    return json(502, { error: "versions_build_failed", detail: String(error) });
  }

  const stored = new Response(body, {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": `public, max-age=${VERSIONS_TTL}`,
      [VERSIONS_BUILT_AT]: String(Date.now()),
    },
  });
  ctx.waitUntil(caches.default.put(cacheKey, stored.clone()));
  return versionsResponse(request, body, stored.headers);
}

function versionsResponse(request, body, headers) {
  const out = new Response(request.method === "HEAD" ? null : body, { headers });
  out.headers.set("cache-control", "public, max-age=3600");
  out.headers.set("access-control-allow-origin", "*");
  return out;
}

async function assembleVersions(env) {
  const releases = await fetchAllReleases(env);
  const groups = new Map();

  for (const rel of releases) {
    if (rel.draft) continue;
    const tag = String(rel.tag_name || "");
    const idx = tag.lastIndexOf("-");
    const version = tag.slice(0, idx);
    const flavor = tag.slice(idx + 1);
    if (!groups.has(version)) groups.set(version, []);
    groups.get(version).push({
      name: flavor,
      release_date: formatDisplayDate(rel.published_at),
      release_notes: rel.html_url || "",
      _ts: String(rel.published_at || ""),
    });
  }

  const out = [];
  for (const [version, list] of groups) {
    // 组内: 通道序 (stable > rc > beta > alpha > dev), 同通道序号大者前,
    // 再按发布时间倒序 —— 与官方 versions.json 的组内顺序一致
    list.sort(
      (a, b) =>
        channelRank(b.name) - channelRank(a.name) ||
        channelNum(b.name) - channelNum(a.name) ||
        (a._ts < b._ts ? 1 : a._ts > b._ts ? -1 : 0)
    );
    out.push({
      name: version,
      releases: list.map(({ name, release_date, release_notes }) => ({
        name,
        release_date,
        release_notes,
      })),
    });
  }
  // 组间: 版本号倒序 (4.8 → 4.7.2 → 4.7 → ... → 1.1), 与官方一致
  out.sort((a, b) => compareVersion(b.name, a.name));
  return out;
}

async function fetchAllReleases(env) {
  const headers = {
    accept: "application/vnd.github+json",
    "user-agent": "godot-download-worker",
  };
  if (env.GITHUB_TOKEN) headers.authorization = `Bearer ${env.GITHUB_TOKEN}`;

  const seen = new Set();
  const merged = [];

  for (const repo of REPOS) {
    for (let page = 1; page <= RELEASE_PAGES_CAP; page++) {
      const batch = await fetchReleasePage(
        `https://api.github.com/repos/${repo}/releases?per_page=100&page=${page}`,
        headers,
        repo,
        page
      );
      if (!Array.isArray(batch) || batch.length === 0) break;
      for (const rel of batch) {
        const tag = String(rel.tag_name || "");
        if (seen.has(tag)) continue;
        // 只收规范版本 tag (4.7.2-stable / 4.8-beta2 / 2.0.4.1-stable),
        // 过滤杂物; 版本号允许多段 (2.0.4.1)
        if (!/^\d+(\.\d+)+-[a-z]+\d*$/i.test(tag)) continue;
        seen.add(tag);
        merged.push(rel);
      }
      if (batch.length < 100) break;
    }
  }
  if (merged.length === 0) {
    throw new Error("no releases parsed from GitHub");
  }
  return merged;
}

async function fetchReleasePage(url, headers, repo, page) {
  // 单次重试: 冷启动首建曾因 GitHub 瞬时抖动整轮失败
  let lastError;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const resp = await fetch(url, { headers });
      if (resp.ok) return resp.json();
      lastError = new Error(`GitHub API ${resp.status} (${repo} p${page})`);
    } catch (error) {
      lastError = new Error(`GitHub API unreachable (${repo} p${page}): ${error}`);
    }
    if (attempt === 0) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
  }
  // 任一页最终失败整体抛出: 由 versionsJson 回退上一份, 不产出半截列表
  throw lastError;
}

function formatDisplayDate(iso) {
  const m = String(iso || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return String(iso || "");
  return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1] || ""} ${m[1]}`;
}

function channelRank(flavor) {
  const channel = String(flavor).replace(/\d+$/, "");
  return { stable: 5, rc: 4, beta: 3, alpha: 2, dev: 1 }[channel] ?? 0;
}

function channelNum(flavor) {
  const m = String(flavor).match(/(\d+)$/);
  return m ? Number(m[1]) : 0;
}

function compareVersion(a, b) {
  const pa = String(a).split(".").map((n) => Number(n) || 0);
  const pb = String(b).split(".").map((n) => Number(n) || 0);
  for (let i = 0; i < 3; i++) {
    const d = (pa[i] || 0) - (pb[i] || 0);
    if (d) return d;
  }
  return 0;
}
