# Godot Asset Library 支持

## 目标

支持从 Godot Asset Library (godotengine.org/asset-library) 搜索和下载插件，与现有 Asset Store 互补。

## 两个插件库对比

| | Godot Asset Store | Godot Asset Library |
|--|-------------------|---------------------|
| URL | `store.godotengine.org` | `godotengine.org/asset-library` |
| API | `store.godotengine.org/api/v1` | `godotengine.org/asset-library/api` |
| 数量 | 较少 | 3258+ |
| 质量 | 官方审核 | 社区提交 |
| 下载 | GitHub Releases | Asset Library 直接链接 |

## API

- 搜索: `GET /asset-library/api/asset?q=xxx&godot_version=4.7`
- 详情: `GET /asset-library/api/asset?id=xxx`

## 实现方案

### 方案 1：优先 Asset Store，回退 Asset Library

```
gdpm search mcp
  → 先搜索 Asset Store
  → 如果没有结果，搜索 Asset Library
```

### 方案 2：指定源

```
gdpm search mcp --source store
gdpm search mcp --source library
gdpm search mcp --source all
```

### 方案 3：合并结果

```
gdpm search mcp --all-sources
```

## 实现步骤

- [ ] 添加 Asset Library API 客户端
- [ ] 修改 `gdpm search` 支持双源搜索
- [ ] 修改 `gdpm add` 支持从 Asset Library 下载
- [ ] 修改 `gdpm info` 显示来源
