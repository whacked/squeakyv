"""
squeakyv - Simple SQLite-backed caching library

A minimal, cross-language key-value cache using SQLite as the storage backend.
Designed for simplicity and maintainability across multiple language implementations.

Basic Usage:
    >>> from squeakyv import CacheClient
    >>> cache = CacheClient("my_cache.db")
    >>> cache.set("key", b"value")
    >>> cache.get("key")
    b'value'
    >>> cache.delete("key")

With context manager:
    >>> with CacheClient("my_cache.db") as cache:
    ...     cache.set("key", b"value")
    ...     value = cache.get("key")

Function memoization:
    >>> from squeakyv import memoize
    >>> @memoize()
    ... def expensive_function(arg: str) -> str:
    ...     return f"result for {arg}"
"""

from .core import CacheClient, KeyNotFoundError, memoize

__version__ = "0.1.0"
__all__ = ["CacheClient", "KeyNotFoundError", "memoize"]
