# squeakyv

A simple, SQLite-backed key-value caching library designed for simplicity and cross-language portability.

## Features

- **Simple API**: Just `get`, `set`, `delete`, and `list_keys`
- **Thread-safe**: Uses thread-local connections for safe concurrent access
- **Zero dependencies**: Pure stdlib, only requires Python 3.9+
- **Version history**: Soft deletes preserve value history
- **Memoization**: Built-in decorator for caching function results
- **In-memory or persistent**: Use `:memory:` for ephemeral cache or file path for persistence

## Installation

```bash
pip install squeakyv
```

## Quick Start

### Basic Usage

```python
from squeakyv import CacheClient

# Create a cache (in-memory by default)
cache = CacheClient()

# Store a value
cache.set("mykey", b"Hello, World!")

# Retrieve a value
value = cache.get("mykey")
print(value)  # b'Hello, World!'

# List all keys
keys = cache.list_keys()
print(keys)  # ['mykey']

# Delete a key
cache.delete("mykey")

# Get with default for missing keys
value = cache.get("nonexistent", default=b"default")
print(value)  # b'default'
```

### Persistent Cache

```python
from squeakyv import CacheClient

# Use a file path for persistent storage
cache = CacheClient("my_cache.db")
cache.set("key", b"value")

# Data persists across restarts
cache2 = CacheClient("my_cache.db")
print(cache2.get("key"))  # b'value'
```

### Context Manager

```python
from squeakyv import CacheClient

with CacheClient("my_cache.db") as cache:
    cache.set("key", b"value")
    value = cache.get("key")
# Connection automatically closed
```

### Function Memoization

```python
from squeakyv import memoize
import os

# Set default cache location (optional)
os.environ["SQUEAKYV_DATABASE"] = "cache.db"

@memoize()
def expensive_function(arg: str) -> str:
    print(f"Computing result for {arg}")
    return f"result for {arg}"

# First call executes function
result = expensive_function("test")  # Prints: Computing result for test

# Second call returns cached result
result = expensive_function("test")  # No print - returned from cache
```

## API Reference

### `CacheClient`

**Constructor**
```python
CacheClient(path: str = ":memory:")
```
- `path`: Database file path. Defaults to `":memory:"` for in-memory cache.

**Methods**

- `get(key: str, default: Any = None) -> bytes | None`
  - Retrieve value for a key
  - Returns `default` if key doesn't exist

- `set(key: str, value: bytes) -> None`
  - Store a value for a key
  - Value must be bytes (use `.encode()` for strings)
  - Creates new version if key exists (old value soft-deleted)

- `delete(key: str) -> None`
  - Delete a key (soft delete - preserves history)

- `list_keys() -> list[str]`
  - List all active keys
  - Ordered by insertion time (newest first)

- `close() -> None`
  - Close thread-local database connection

**Context Manager**
```python
with CacheClient("db.db") as cache:
    cache.set("key", b"value")
```

### `memoize`

**Decorator**
```python
@memoize(key_prefix: Optional[str] = None)
def function(arg: str) -> str:
    ...
```
- `key_prefix`: Optional cache key prefix (defaults to function's qualified name)
- **Limitation**: Only supports `str` arguments and `str` return values
- For complex types, use `CacheClient` directly with custom serialization

### `KeyNotFoundError`

Exception raised when accessing non-existent keys (currently not used, reserved for future strict mode).

## Thread Safety

`CacheClient` is thread-safe through thread-local connections. Each thread gets its own SQLite connection, avoiding concurrency issues.

```python
from threading import Thread
from squeakyv import CacheClient

cache = CacheClient("shared.db")

def worker(i):
    cache.set(f"key{i}", f"value{i}".encode())
    print(cache.get(f"key{i}"))

threads = [Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Data Storage

Values are stored as **raw bytes**. For structured data:

```python
import json
import pickle

# JSON (strings only)
cache.set("data", json.dumps({"key": "value"}).encode())
data = json.loads(cache.get("data").decode())

# Pickle (any Python object)
cache.set("object", pickle.dumps({"complex": [1, 2, 3]}))
obj = pickle.loads(cache.get("object"))
```

## Version History

`squeakyv` uses soft deletes, preserving value history. When you update a key, the old value is marked inactive but remains in the database. This enables:

- Audit trails
- Time-travel queries (future feature)
- Rollback capabilities (future feature)

Current API only exposes active values. Historical queries will be added in future versions.

## Cross-Language Design

`squeakyv` is designed for consistent semantics across multiple languages. The Python implementation uses code generation from a shared schema definition, ensuring identical behavior when implemented in Go, Ruby, Clojure, Bash, etc.

**Core principles:**
- Minimal features that work everywhere
- Raw bytes storage (no language-specific serialization)
- Simple, stateless operations
- SQLite as the universal backend

## Performance Notes

- Thread-local connections minimize locking overhead
- Autocommit mode (`isolation_level=None`) for faster writes
- Indexes on `(key, is_active)` for efficient lookups
- In-memory mode (`:memory:`) for maximum performance

## Limitations

- Values must be bytes (no automatic serialization)
- No TTL/expiration support (keep design simple)
- No namespacing (single flat keyspace)
- Memoize decorator limited to string args/returns
- No async support (use `aiosqlite` wrapper if needed)

## Development

This package is auto-generated from a schema definition using a custom build pipeline:

1. Schema definition (Jsonnet) → JSON Schema
2. JSON Schema → SQL DDL
3. JSON Schema → YeSQL query templates
4. YeSQL → Python code (via language-specific renderer)

To rebuild:
```bash
# Run the build pipeline (requires sdflow)
sdflow generate-python-target
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! This is a simple library by design - please keep PRs focused on:
- Bug fixes
- Performance improvements
- Documentation improvements
- Cross-language consistency

Avoid adding language-specific features that can't be replicated across all target languages.
