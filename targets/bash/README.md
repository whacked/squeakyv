# squeakyv - Bash Implementation

Simple SQLite-backed key-value cache for Bash scripts. Provides the same semantics as other squeakyv implementations.

## Requirements

- Bash 4.0+ (for `set -euo pipefail` and parameter expansion)
- `sqlite3` CLI tool (universally available on Unix systems)

## Installation

Simply source the library in your script:

```bash
source /path/to/squeakyv.sh
```

Or copy `squeakyv.sh` into your project.

## Quick Start

```bash
#!/usr/bin/env bash
source squeakyv.sh

# Create/initialize database
DB="my_cache.db"
squeakyv_init_db "$DB"

# Set a value
squeakyv_set_value "$DB" "mykey" "myvalue"

# Get a value
value=$(squeakyv_get_current_value "$DB" "mykey")
echo "Retrieved: $value"

# List all keys
squeakyv_list_active_keys "$DB"

# Delete a key
squeakyv_delete_key "$DB" "mykey"
```

## API Reference

All functions take `db_path` as the first argument. Values are stored as text.

### `squeakyv_init_db <db_path>`

Initialize the database schema. Idempotent - safe to call multiple times.

```bash
squeakyv_init_db "cache.db"
```

### `squeakyv_set_value <db_path> <key> <value>`

Store a value for a key. If the key exists, creates a new version (old value soft-deleted).

```bash
squeakyv_set_value "cache.db" "mykey" "myvalue"
```

### `squeakyv_get_current_value <db_path> <key>`

Retrieve the current value for a key. Returns empty string if key doesn't exist.

```bash
value=$(squeakyv_get_current_value "cache.db" "mykey")
if [[ -z "$value" ]]; then
    echo "Key not found"
fi
```

### `squeakyv_list_active_keys <db_path>`

List all active keys, one per line, newest first.

```bash
squeakyv_list_active_keys "cache.db" | while read -r key; do
    echo "Found key: $key"
done
```

### `squeakyv_delete_key <db_path> <key>`

Delete a key (soft delete - marks as inactive).

```bash
squeakyv_delete_key "cache.db" "mykey"
```

## Usage Examples

### Simple Configuration Cache

```bash
#!/usr/bin/env bash
source squeakyv.sh

CONFIG_DB="$HOME/.config/myapp/cache.db"
squeakyv_init_db "$CONFIG_DB"

# Store configuration
squeakyv_set_value "$CONFIG_DB" "api_endpoint" "https://api.example.com"
squeakyv_set_value "$CONFIG_DB" "timeout" "30"

# Retrieve configuration
endpoint=$(squeakyv_get_current_value "$CONFIG_DB" "api_endpoint")
timeout=$(squeakyv_get_current_value "$CONFIG_DB" "timeout")

echo "Using endpoint: $endpoint with timeout: ${timeout}s"
```

### Caching Expensive Operations

```bash
#!/usr/bin/env bash
source squeakyv.sh

CACHE_DB="/tmp/build_cache.db"
squeakyv_init_db "$CACHE_DB"

cache_key="build_$(git rev-parse HEAD)"

# Check cache
cached_result=$(squeakyv_get_current_value "$CACHE_DB" "$cache_key")

if [[ -n "$cached_result" ]]; then
    echo "Using cached build result"
    echo "$cached_result"
else
    echo "Running build..."
    result=$(make build 2>&1)

    # Cache the result
    squeakyv_set_value "$CACHE_DB" "$cache_key" "$result"
    echo "$result"
fi
```

### Temporary State Storage

```bash
#!/usr/bin/env bash
source squeakyv.sh

STATE_DB="/tmp/script_state_$$.db"
trap "rm -f $STATE_DB" EXIT

squeakyv_init_db "$STATE_DB"

# Store intermediate results
for i in {1..10}; do
    result=$(expensive_computation "$i")
    squeakyv_set_value "$STATE_DB" "step_$i" "$result"
done

# Process all results
squeakyv_list_active_keys "$STATE_DB" | while read -r key; do
    value=$(squeakyv_get_current_value "$STATE_DB" "$key")
    process_result "$value"
done
```

## Debug Mode

Enable debug output by setting `SQUEAKYV_DEBUG`:

```bash
export SQUEAKYV_DEBUG=1
source squeakyv.sh

squeakyv_set_value "test.db" "key" "value"
# Outputs:
# [DEBUG] SQL: INSERT INTO kv (key, value) VALUES (:key, :value);
# [DEBUG] Input: .param set :key 'key'
# .param set :value 'value'
# INSERT INTO kv (key, value) VALUES (:key, :value);
```

## Thread Safety

Bash functions execute in subshells, and SQLite handles concurrent access via file locking. Multiple processes can safely access the same database file.

## Limitations

- **Text values only**: Binary data requires base64 encoding/decoding
- **No TTL/expiration**: Keep design simple and cross-language compatible
- **No namespacing**: Single flat keyspace per database
- **String escaping**: Values with single quotes are properly escaped by `.param` command
- **Performance**: Subprocess overhead - not suitable for high-frequency access (use Python/Go for performance-critical use cases)

## Data Storage

Unlike the Python implementation which stores bytes, the Bash version stores TEXT values. For structured data:

```bash
# JSON (requires jq)
json_data='{"name":"value","count":42}'
squeakyv_set_value "$DB" "config" "$json_data"

retrieved=$(squeakyv_get_current_value "$DB" "config")
name=$(echo "$retrieved" | jq -r '.name')

# Base64 for binary data
base64_data=$(cat image.png | base64)
squeakyv_set_value "$DB" "image" "$base64_data"

squeakyv_get_current_value "$DB" "image" | base64 -d > restored.png
```

## Version History

Like all squeakyv implementations, this uses soft deletes. Updated values create new versions while keeping old ones inactive. The current API only exposes active values.

## Design Philosophy

This Bash implementation prioritizes:
- **Simplicity**: Pure bash + sqlite3 CLI
- **Portability**: Works on any Unix system with bash + sqlite3
- **Consistency**: Same semantics as Python/Go/Ruby implementations
- **Demo/testing**: Great for CI scripts, testing, automation

For production workloads, use Python or Go implementations.

## Testing

Run the included test suite:

```bash
./test_squeakyv.sh
```

## Cross-Language Compatibility

This implementation shares the same database schema and semantics with:
- Python (most features, best performance)
- Go (coming soon - compiled performance)
- Ruby (coming soon - scripting convenience)
- Clojure (coming soon - functional approach)

You can mix and match - write data in bash, read in Python, etc.
