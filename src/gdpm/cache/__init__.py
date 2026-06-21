"""Cache management."""

from gdpm.cache.file_cache import FileCache
from gdpm.cache.protocol import CacheProtocol

__all__ = ["CacheProtocol", "FileCache"]
