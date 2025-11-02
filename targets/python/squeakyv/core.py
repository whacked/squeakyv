"""
Core CacheClient implementation for squeakyv.
Provides thread-safe SQLite-backed key-value caching.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any, Optional

from . import _operations


class KeyNotFoundError(Exception):
    """Raised when attempting to access a non-existent key."""
    pass


class CacheClient:
    """
    Thread-safe SQLite-backed key-value cache client.

    Uses thread-local connections for safe concurrent access.
    Supports context manager protocol for automatic cleanup.

    Example:
        >>> cache = CacheClient("my_cache.db")
        >>> cache.set("mykey", b"myvalue")
        >>> cache.get("mykey")
        b'myvalue'
        >>> cache.delete("mykey")
        >>> cache.get("mykey", default=None)
        None
    """

    def __init__(self, path: str = ":memory:"):
        """
        Initialize a new cache client.

        Args:
            path: Database file path. Defaults to ":memory:" for in-memory cache.
                  Use an explicit path for persistent caching.
        """
        self.path = path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """
        Get or create a thread-local database connection.

        Returns:
            sqlite3.Connection: Thread-local connection instance
        """
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(
                self.path,
                timeout=30.0,
                isolation_level=None,  # autocommit mode
                check_same_thread=False,
            )
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        """
        Initialize database schema from embedded SQL.

        Uses the schema SQL string embedded in the _operations module
        and executes it to create tables, indexes, triggers, and views.
        """
        conn = self._get_conn()

        # Import embedded schema SQL from generated module
        if not hasattr(_operations, 'SCHEMA_SQL'):
            raise RuntimeError(
                "SCHEMA_SQL not found in _operations module. "
                "Package may be corrupted or not properly built. "
                "Run the build pipeline to regenerate: sdflow generate-python-target"
            )

        conn.executescript(_operations.SCHEMA_SQL)

    def get(self, key: str, default: Any = None) -> bytes | None:
        """
        Retrieve value for a key.

        Args:
            key: The key to retrieve
            default: Value to return if key doesn't exist (default: None)

        Returns:
            The stored bytes value, or default if key not found
        """
        conn = self._get_conn()
        result = _operations._get_current_value(conn, key)

        if result is None:
            return default

        return result

    def set(self, key: str, value: bytes) -> None:
        """
        Store a value for a key.

        If the key already exists, a new version is created and the old
        value is deactivated (soft delete with version history).

        Args:
            key: The key to store
            value: The bytes value to store

        Raises:
            TypeError: If value is not bytes
        """
        if not isinstance(value, bytes):
            raise TypeError(
                f"Value must be bytes, got {type(value).__name__}. "
                "Use value.encode() for strings or pickle.dumps() for objects."
            )

        conn = self._get_conn()
        _operations._set_value(conn, key, value)

    def delete(self, key: str) -> None:
        """
        Delete a key (soft delete - marks as inactive).

        Args:
            key: The key to delete

        Note:
            This is a soft delete. The value remains in the database
            for version history but is marked inactive.
        """
        conn = self._get_conn()
        _operations._delete_key(conn, key)

    def list_keys(self) -> list[str]:
        """
        List all active keys.

        Returns:
            List of all active key names, ordered by insertion time (newest first)
        """
        conn = self._get_conn()
        return _operations._list_active_keys(conn)

    def close(self) -> None:
        """
        Close the thread-local database connection.

        Note:
            This only closes the connection for the current thread.
            Other threads' connections remain open.
        """
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            del self._local.conn

    def __enter__(self) -> CacheClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes connection."""
        self.close()

    def __repr__(self) -> str:
        return f"CacheClient(path={self.path!r})"


def memoize(key_prefix: Optional[str] = None):
    """
    Decorator to memoize function results in the global cache.

    Caches function results based on string representation of arguments.
    IMPORTANT: Only works for functions with str arguments and str return values.

    Args:
        key_prefix: Optional prefix for cache keys. If None, uses function's qualified name.

    Returns:
        Decorator function

    Example:
        >>> @memoize()
        ... def expensive_function(arg: str) -> str:
        ...     # expensive computation
        ...     return result
        >>>
        >>> # First call executes function
        >>> result = expensive_function("input")
        >>>
        >>> # Second call returns cached result
        >>> result = expensive_function("input")

    Note:
        - Uses a global default CacheClient instance (in-memory by default)
        - Override default path with SQUEAKYV_DATABASE environment variable
        - For complex types, implement custom caching using CacheClient directly
    """
    def decorator(fn):
        prefix = key_prefix or f"{fn.__module__}.{fn.__qualname__}"

        def wrapper(*args, **kwargs):
            # Simple key generation from args
            # This is intentionally basic - complex use cases should use CacheClient directly
            if kwargs:
                key_parts = [prefix] + [repr(a) for a in args] + [f"{k}={v!r}" for k, v in sorted(kwargs.items())]
            else:
                key_parts = [prefix] + [repr(a) for a in args]

            cache_key = ":".join(key_parts)

            # Check cache
            cache = _get_default_cache()
            cached = cache.get(cache_key, default=None)

            if cached is not None:
                return cached.decode('utf-8')

            # Execute function
            result = fn(*args, **kwargs)

            # Cache result (only if it's a string)
            if isinstance(result, str):
                cache.set(cache_key, result.encode('utf-8'))

            return result

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        wrapper.__wrapped__ = fn

        return wrapper

    return decorator


# Global default cache instance (lazy initialization)
_default_cache: Optional[CacheClient] = None


def _get_default_cache() -> CacheClient:
    """
    Get or create the global default cache instance.

    The default cache uses:
    - SQUEAKYV_DATABASE environment variable if set
    - Otherwise defaults to :memory: (non-persistent)

    Returns:
        Global CacheClient instance
    """
    global _default_cache

    if _default_cache is None:
        path = os.getenv("SQUEAKYV_DATABASE", ":memory:")
        _default_cache = CacheClient(path)

    return _default_cache
