"""
缓存管理包, 提供插件 zip 包的本地文件缓存与索引管理.

----

Note:
    - FileCache: 基于文件系统的缓存实现.
    - CacheProtocol: 依赖注入用的缓存接口.
"""

from gdpm.cache.file_cache import FileCache
from gdpm.cache.protocol import CacheProtocol

__all__ = ["CacheProtocol", "FileCache"]
