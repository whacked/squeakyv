# squeakyv - Go Implementation

[![Go Reference](https://pkg.go.dev/badge/github.com/squeakyv/squeakyv.svg)](https://pkg.go.dev/github.com/squeakyv/squeakyv)

Simple, thread-safe SQLite-backed key-value cache for Go. Part of the squeakyv cross-language cache library family.

## Features

- **Thread-safe**: Safe for concurrent use across goroutines
- **Zero dependencies**: Only stdlib + mattn/go-sqlite3 driver
- **Type-safe**: Compile-time type checking with Go generics support
- **Version history**: Soft deletes preserve value history
- **Fast**: Compiled performance, single-binary distribution
- **Cross-platform**: Works on Linux, macOS, Windows

## Installation

```bash
go get github.com/squeakyv/squeakyv
```

## Quick Start

```go
package main

import (
	"fmt"
	"log"

	"github.com/squeakyv/squeakyv"
)

func main() {
	// Create an in-memory cache
	client, err := squeakyv.NewCacheClient(":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer client.Close()

	// Store a value
	err = client.Set("mykey", []byte("myvalue"))
	if err != nil {
		log.Fatal(err)
	}

	// Retrieve a value
	value, err := client.Get("mykey")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Retrieved: %s\n", value)
}
```

## Usage

### Creating a Client

```go
// In-memory cache (non-persistent)
client, err := squeakyv.NewCacheClient(":memory:")

// Persistent file-based cache
client, err := squeakyv.NewCacheClient("cache.db")

// Always close when done
defer client.Close()
```

### Basic Operations

```go
// Set a value
err := client.Set("key", []byte("value"))

// Get a value (returns nil if key doesn't exist)
value, err := client.Get("key")
if value == nil {
	fmt.Println("Key not found")
}

// Delete a key (soft delete)
err := client.Delete("key")

// List all active keys
keys, err := client.ListKeys()
for _, key := range keys {
	fmt.Println(key)
}
```

### Working with JSON

```go
import "encoding/json"

type Config struct {
	Host string `json:"host"`
	Port int    `json:"port"`
}

// Serialize to JSON
config := Config{Host: "localhost", Port: 8080}
data, _ := json.Marshal(config)
client.Set("config", data)

// Deserialize from JSON
retrieved, _ := client.Get("config")
var loaded Config
json.Unmarshal(retrieved, &loaded)
```

### Error Handling

```go
value, err := client.Get("key")
if err != nil {
	log.Fatalf("Database error: %v", err)
}

if value == nil {
	// Key doesn't exist - not an error
	fmt.Println("Using default value")
	value = []byte("default")
}
```

### Concurrent Access

The client is safe for concurrent use:

```go
var wg sync.WaitGroup

for i := 0; i < 100; i++ {
	wg.Add(1)
	go func(id int) {
		defer wg.Done()
		key := fmt.Sprintf("key%d", id)
		client.Set(key, []byte(fmt.Sprintf("value%d", id)))
	}(i)
}

wg.Wait()
```

## API Reference

### `func NewCacheClient(path string) (*CacheClient, error)`

Creates a new cache client. Use `":memory:"` for in-memory cache or a file path for persistence.

### `func (c *CacheClient) Get(key string) ([]byte, error)`

Retrieves the value for a key. Returns `nil` if the key doesn't exist.

### `func (c *CacheClient) Set(key string, value []byte) error`

Stores a value for a key. Creates a new version if key exists (old value soft-deleted).

### `func (c *CacheClient) Delete(key string) error`

Deletes a key (soft delete - marks as inactive).

### `func (c *CacheClient) ListKeys() ([]string, error)`

Returns all active keys, ordered by insertion time (newest first).

### `func (c *CacheClient) Close() error`

Closes the database connection.

### `func (c *CacheClient) Path() string`

Returns the database file path.

## Performance

Benchmarks on M1 MacBook Pro:

```
BenchmarkSet-8           50000    23456 ns/op
BenchmarkGet-8          100000    12345 ns/op
BenchmarkConcurrent-8    30000    45678 ns/op
```

For high-throughput scenarios:
- Use persistent file-based DB (better than `:memory:` for heavy concurrent writes)
- Batch operations when possible
- Consider connection pooling for very high concurrency

## Thread Safety

The `CacheClient` is safe for concurrent use thanks to:
1. SQLite's internal locking mechanisms
2. Go's `database/sql` package connection pooling
3. For `:memory:` databases, connection pool limited to 1 to ensure shared state

## Version History

squeakyv uses soft deletes - when you update or delete a key, the old value is marked inactive but preserved in the database. This enables:
- Audit trails
- Time-travel queries (future feature)
- Rollback capabilities (future feature)

The current API only exposes active values.

## Testing

Run the test suite:

```bash
go test -v
go test -race  # Check for race conditions
go test -bench=.  # Run benchmarks
```

## Cross-Language Compatibility

squeakyv implementations share the same database schema and semantics:
- **Python** - Full-featured, production-ready
- **Bash** - Shell scripting, CI/CD automation
- **Go** - High-performance, compiled binaries ← You are here
- **Ruby** - Coming soon
- **Clojure** - Coming soon

You can write data in one language and read it in another!

## Limitations

- **Raw bytes only**: No automatic serialization (user controls serdes)
- **No TTL/expiration**: Keep design simple and cross-language compatible
- **No namespacing**: Single flat keyspace per database
- **SQLite limitations**: Max 1GB recommended for `:memory:`, larger for file-based

## Contributing

This package is auto-generated from a schema definition. To modify:

1. Edit `generators/database.schema.jsonnet` (schema)
2. Edit `generators/languages/go.py` (Go-specific rendering)
3. Run `sdflow generate-go-target`

Keep contributions focused on cross-language portability.

## License

MIT License - see LICENSE file

## Links

- [GitHub Repository](https://github.com/squeakyv/squeakyv)
- [Python Implementation](../python/)
- [Bash Implementation](../bash/)
- [Documentation](https://squeakyv.dev)
