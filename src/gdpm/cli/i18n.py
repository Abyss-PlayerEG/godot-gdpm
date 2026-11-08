"""
帮助文案多语言 (i18n)

- 词典是帮助文案的唯一事实源: 命令描述 / 分类名 / 示例标签 / 渲染标签.
- 回退链: 目标语言 -> en -> 键名 (缺词条返回键名, 响亮暴露不静默).
- 语言优先级: GDPM_LANG 环境变量 > 配置 [ui] language > 默认 en.

----

Examples
----
    t("list", "zh")        # '列出已安装的插件'
    t("list", "fr")        # 回退英文: 'List installed plugins'
    t("no.such.key")       # 回退键名: 'no.such.key'

Notes
----
- SUPPORTED_LANGUAGES / DEFAULT_LANGUAGE: 已支持语言与默认语言.
- get_language: 解析当前目标语言 (环境变量优先, 进程内缓存).
- t: 词条查询, 按回退链返回文案.
- category_keys: 分类键的展示顺序 (词典定义序).
- _COMMANDS: 命令描述词典 (键 = 根命令裸名 / 组前缀点号路径).
- _CATEGORIES: 分类名词典 (含兜底 other).
- _EXAMPLE_LABELS: 示例标签词典 (键 = 英文原文, en 即键名).
- _UI: 渲染标签词典 (面板标题 / 表头 / 公共选项 / about 屏 / 默认值后缀).
"""

from __future__ import annotations

import os
from functools import cache

from gdpm.config.global_config import read_global_config

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "zh")
DEFAULT_LANGUAGE = "en"

# 命令描述: 根命令用裸名, 子命令用 "组.子命令" 点号路径 (避免 list/info 撞键)
_COMMANDS: dict[str, dict[str, str]] = {
    # 根命令 (Project)
    "init": {"en": "Initialize a new gdpm project", "zh": "初始化新的 gdpm 项目"},
    "create": {"en": "Create a new Godot project", "zh": "创建新的 Godot 项目"},
    "sync": {
        "en": "Sync addons/ to lock file state",
        "zh": "将 addons/ 同步到锁文件状态",
    },
    "lock": {"en": "Generate or update lock file", "zh": "生成或更新锁文件"},
    "list": {"en": "List installed plugins", "zh": "列出已安装的插件"},
    "status": {"en": "Show plugin status and updates", "zh": "显示插件状态与可用更新"},
    # 根命令 (Dependencies)
    "add": {"en": "Add plugins to the project", "zh": "添加一个或多个插件到项目"},
    "remove": {"en": "Remove plugins", "zh": "从项目移除一个或多个插件"},
    "update": {"en": "Update plugins to newer versions", "zh": "将插件更新到较新版本"},
    "search": {
        "en": "Search Godot Asset Store",
        "zh": "在 Godot Asset Store 中搜索插件",
    },
    "info": {"en": "Show plugin details", "zh": "显示插件的详细信息"},
    "cache": {"en": "Manage global cache (info, clean)", "zh": "管理全局缓存"},
    "export": {"en": "Export plugins to zip archive", "zh": "导出插件到 zip 归档"},
    "import": {
        "en": "Import plugins from zip archive",
        "zh": "从 zip 归档或目录导入插件",
    },
    "godot": {"en": "Manage Godot engine versions", "zh": "管理 Godot 引擎版本"},
    "config": {"en": "Manage gdpm global configuration", "zh": "管理全局配置"},
    # godot 组子命令
    "godot.list": {"en": "List Godot engine versions", "zh": "列出 Godot 引擎版本"},
    "godot.install": {
        "en": "Install a Godot engine version",
        "zh": "安装一个 Godot 引擎版本",
    },
    "godot.uninstall": {
        "en": "Uninstall a Godot engine version",
        "zh": "卸载一个 Godot 引擎版本",
    },
    "godot.open": {
        "en": "Open Godot editor for the current project",
        "zh": "为当前项目打开 Godot 编辑器",
    },
    "godot.info": {
        "en": "Show current Godot engine info",
        "zh": "显示当前 Godot 引擎配置",
    },
    "godot.add": {"en": "Add a local Godot engine", "zh": "添加本地 Godot 引擎"},
    "godot.remove": {"en": "Remove a local Godot engine", "zh": "移除本地 Godot 引擎"},
    "godot.use": {
        "en": "Set the Godot engine for the current project",
        "zh": "为当前项目设置 Godot 引擎",
    },
    "godot.default": {
        "en": "Set or show the default Godot engine",
        "zh": "设置或显示默认 Godot 引擎",
    },
    # config 组子命令
    "config.set": {
        "en": "Set a global config value",
        "zh": "设置全局配置项 (空值恢复默认)",
    },
    "config.open": {"en": "Open the config directory", "zh": "打开配置文件所在目录"},
    # cache 组子命令
    "cache.info": {"en": "Show cache info", "zh": "显示缓存信息"},
    "cache.clean": {"en": "Clean all cached files", "zh": "清理全部缓存文件"},
}

# 分类名: 键即命令侧 category= 的取值, 顺序即主帮助展示顺序
_CATEGORIES: dict[str, dict[str, str]] = {
    "project": {"en": "Project", "zh": "项目"},
    "dependencies": {"en": "Dependencies", "zh": "依赖"},
    "engine": {"en": "Engine", "zh": "引擎"},
    "config": {"en": "Config", "zh": "配置"},
    "other": {"en": "Other", "zh": "其他"},
}

# 示例标签: 键 = examples= 里的英文原文 (英文即键名, 无需重复存 en)
_EXAMPLE_LABELS: dict[str, dict[str, str]] = {
    "Add plugin from Godot Store": {"zh": "从 Godot 商店添加插件"},
    "Add with publisher/slug": {"zh": "使用 发布者/slug 添加"},
    "Add specific version": {"zh": "添加指定版本"},
    "Add with version constraint": {"zh": "使用版本约束添加"},
    "Add as dev dependency": {"zh": "作为开发依赖添加"},
    "Pack all local plugins": {"zh": "打包全部本地插件"},
    "Install from zip file": {"zh": "从 zip 文件安装"},
    "Show cache size and location": {"zh": "显示缓存大小与位置"},
    "Clean all cached files": {"zh": "清理全部缓存文件"},
    "Clean without confirmation": {"zh": "跳过确认直接清理"},
    "Set default engine": {"zh": "设置默认引擎"},
    "Open config directory": {"zh": "打开配置目录"},
    "Set parallel downloads": {"zh": "设置并行下载数"},
    "Switch help language (en/zh)": {"zh": "切换帮助语言 (en/zh)"},
    "Reset cache dir to default": {"zh": "将缓存目录恢复为默认"},
    "Interactive create": {"zh": "交互式创建"},
    "Create with name": {"zh": "指定名称创建"},
    "Create and open Godot": {"zh": "创建并打开 Godot"},
    "Export to default location": {"zh": "导出到默认位置"},
    "Export to custom file": {"zh": "导出到自定义文件"},
    "Export to specific path": {"zh": "导出到指定路径"},
    "List installed Godot versions": {"zh": "列出已安装的 Godot 版本"},
    "List available versions": {"zh": "列出可用版本"},
    "Install Godot 4.7": {"zh": "安装 Godot 4.7"},
    "Add macOS Godot": {"zh": "添加 macOS Godot"},
    "Add Linux Godot": {"zh": "添加 Linux Godot"},
    "Add with alias": {"zh": "添加并指定别名"},
    "Remove by name": {"zh": "按名称移除"},
    "Remove by ID": {"zh": "按 ID 移除"},
    "Use downloaded engine": {"zh": "使用已下载的引擎"},
    "Use local engine": {"zh": "使用本地引擎"},
    "List available engine IDs": {"zh": "列出可用引擎 ID"},
    "Show current default engine": {"zh": "显示当前默认引擎"},
    "Remove default engine": {"zh": "移除默认引擎"},
    "Show current Godot engine info": {"zh": "显示当前 Godot 引擎信息"},
    "Install latest 4.7 stable": {"zh": "安装最新的 4.7 稳定版"},
    "Install C# version": {"zh": "安装 C# 版本"},
    "Install specific version": {"zh": "安装指定版本"},
    "Uninstall Godot 4.7": {"zh": "卸载 Godot 4.7"},
    "Uninstall Godot 4.7 C#": {"zh": "卸载 Godot 4.7 C# 版本"},
    "List installed versions": {"zh": "列出已安装版本"},
    "Filter installed versions": {"zh": "筛选已安装版本"},
    "Open Godot editor": {"zh": "打开 Godot 编辑器"},
    "Open a specific engine by ID": {"zh": "按 ID 打开指定引擎"},
    "Run the project": {"zh": "运行项目"},
    "Import from zip archive": {"zh": "从 zip 归档导入"},
    "Import from directory": {"zh": "从目录导入"},
    "Import without confirmation": {"zh": "跳过确认直接导入"},
    "Show plugin details": {"zh": "显示插件详情"},
    "Show with publisher/slug": {"zh": "使用 发布者/slug 查看"},
    "Initialize with auto-detected settings": {"zh": "初始化并自动检测设置"},
    "List all installed plugins": {"zh": "列出全部已安装插件"},
    "Output as JSON": {"zh": "以 JSON 格式输出"},
    "Generate lock file": {"zh": "生成锁文件"},
    "Check if lock file is up to date": {"zh": "检查锁文件是否为最新"},
    "Remove a plugin": {"zh": "移除插件"},
    "Remove without confirmation": {"zh": "跳过确认直接移除"},
    "Remove with sub-dependencies": {"zh": "同时移除未使用的子依赖"},
    "Search for MCP plugins": {"zh": "搜索 MCP 插件"},
    "Show top 5 results": {"zh": "显示前 5 条结果"},
    "Include templates": {"zh": "包含模板"},
    "Sort by downloads": {"zh": "按下载量排序"},
    "Show status of all plugins": {"zh": "显示全部插件状态"},
    "Show status of specific plugin": {"zh": "显示指定插件状态"},
    "Sync all plugins": {"zh": "同步全部插件"},
    "Preview changes without applying": {"zh": "预览变更但不应用"},
    "Strict mode for CI": {"zh": "CI 严格模式"},
    "Update all plugins": {"zh": "更新全部插件"},
    "Update specific plugin": {"zh": "更新指定插件"},
    "Preview updates": {"zh": "预览更新"},
    "Ignore version constraints": {"zh": "忽略版本约束"},
}

# 渲染标签: 帮助界面的结构性文案 (面板标题/表头/公共选项)
_UI: dict[str, dict[str, str]] = {
    "ui.commands": {"en": "Commands", "zh": "命令"},
    "ui.options": {"en": "Options", "zh": "选项"},
    "ui.examples": {"en": "Examples", "zh": "示例"},
    "ui.common_options": {"en": "Common Options", "zh": "公共选项"},
    "ui.usage": {"en": "Usage:", "zh": "用法:"},
    "ui.help": {"en": "Help:", "zh": "帮助:"},
    "ui.option": {"en": "Option", "zh": "选项"},
    "ui.description": {"en": "Description", "zh": "说明"},
    "ui.command": {"en": "Command", "zh": "命令"},
    "ui.opt_help": {"en": "Show help message", "zh": "显示帮助信息"},
    "ui.opt_about": {
        "en": "Show about information (version, repo, contributors)",
        "zh": "显示关于信息 (版本、仓库、贡献者)",
    },
    "ui.about_title": {"en": "GDPM-About", "zh": "GDPM 关于"},
    "ui.tagline": {
        "en": "Godot Dependency Package Manager",
        "zh": "Godot 依赖包管理器",
    },
    "ui.developer": {"en": "Developer:", "zh": "开发者:"},
    "ui.contributors": {"en": "Contributors", "zh": "贡献者"},
    "ui.opt_version": {"en": "Show version", "zh": "显示版本"},
    "ui.opt_yes": {"en": "Skip confirmation prompts", "zh": "跳过确认提示"},
    "ui.default": {"en": "(default: {v})", "zh": "(默认: {v})"},
    "ui.default_on": {"en": "(default: on)", "zh": "(默认: 开启)"},
}


def _normalize(lang: str) -> str:
    """
    归一化语言代码: 去空白并转小写, 截断地区后缀.

    ----

    Parameters
    ----
    lang : str
        原始语言代码, 如 'ZH_CN' / 'zh-CN' / ' zh '.

    Returns
    ----
    str
        归一化结果, 如 'zh'.
    """
    return lang.strip().lower().split("-")[0].split("_")[0]


@cache
def get_language() -> str:
    """
    解析当前目标语言 (进程内缓存, 测试可用 cache_clear 重置).

    优先级: GDPM_LANG 环境变量 > 配置 [ui] language > 默认 en.
    不支持的语言代码原样返回, 由 t() 按回退链降级为英文.

    ----

    Returns
    ----
    str
        目标语言代码.
    """
    env = os.environ.get("GDPM_LANG", "")
    if env.strip():
        return _normalize(env)
    configured = read_global_config().language
    return _normalize(configured) if configured else DEFAULT_LANGUAGE


def t(key: str, lang: str | None = None) -> str:
    """
    词条查询: 按 回退链 目标语言 -> en -> 键名 返回文案.

    ----

    Parameters
    ----
    key : str
        词典键 (命令键 / 分类键 / 示例标签英文原文 / ui.* 渲染标签).
    lang : str | None, optional
        目标语言, None 时取 get_language().

    Returns
    ----
    str
        对应语言的文案; 词条缺失时返回英文, 键整体缺失时返回键名本身.
    """
    language = lang if lang is not None else get_language()
    for table in (_COMMANDS, _CATEGORIES, _EXAMPLE_LABELS, _UI):
        entry = table.get(key)
        if entry is not None:
            text = entry.get(language) or entry.get(DEFAULT_LANGUAGE)
            return text if text else key
    return key


def category_keys() -> tuple[str, ...]:
    """
    分类键的展示顺序 (词典定义序, 兜底 other 恒在最后).

    ----

    Returns
    ----
    tuple[str, ...]
        分类键元组.
    """
    return tuple(_CATEGORIES)


def category_name(key: str, lang: str | None = None) -> str:
    """
    分类名查询 (独立命名空间, 不走 t() 的命令优先链).

    分类键 config 与根命令 config 同名, 混在 t() 里会被命令词条顶掉,
    因此分类展示一律走本函数.

    ----

    Parameters
    ----
    key : str
        分类键 (project / dependencies / engine / config / other).
    lang : str | None, optional
        目标语言, None 时取 get_language().

    Returns
    ----
    str
        分类展示名; 键缺失时返回键名本身.
    """
    language = lang if lang is not None else get_language()
    entry = _CATEGORIES.get(key)
    if entry is None:
        return key
    text = entry.get(language) or entry.get(DEFAULT_LANGUAGE)
    return text if text else key
