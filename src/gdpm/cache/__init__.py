"""
缓存管理包, 提供插件 zip 包的本地文件缓存与索引管理.

Cache management package. Provide local file caching and index management
for plugin zip archives.

----

Note:
    - FileCache: 基于文件系统的缓存实现 / File-system based cache implementation.
    - CacheProtocol: 依赖注入用的缓存接口 / Cache interface for injection.
"""

from gdpm.cache.file_cache import FileCache
from gdpm.cache.protocol import CacheProtocol

__all__ = ["CacheProtocol", "FileCache"]
