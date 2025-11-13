// Package squeakyv provides a simple SQLite-backed key-value cache.
//
// This package offers thread-safe caching with version history support.
// Values are stored as raw bytes, giving you full control over serialization.
//
// Basic usage:
//
//	client, err := squeakyv.NewCacheClient(":memory:")
//	if err != nil {
//		log.Fatal(err)
//	}
//	defer client.Close()
//
//	// Set a value
//	err = client.Set("mykey", []byte("myvalue"))
//
//	// Get a value
//	value, err := client.Get("mykey")
//
//	// Delete a key
//	err = client.Delete("mykey")
package squeakyv

import (
	"database/sql"
	"fmt"
	"sync"

	_ "github.com/mattn/go-sqlite3"
)

// CacheClient provides thread-safe access to a SQLite-backed key-value cache.
//
// Each CacheClient maintains a single database connection. The client is safe
// for concurrent use by multiple goroutines thanks to SQLite's internal locking.
type CacheClient struct {
	db   *sql.DB
	path string
	mu   sync.Mutex
}

// NewCacheClient creates a new cache client with the specified database path.
//
// Use ":memory:" for an in-memory cache, or provide a file path for persistent storage.
// The database schema is automatically initialized if it doesn't exist.
//
// Example:
//
//	client, err := squeakyv.NewCacheClient("cache.db")
//	if err != nil {
//		return err
//	}
//	defer client.Close()
func NewCacheClient(path string) (*CacheClient, error) {
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// For :memory: databases, limit to single connection to share the same in-memory DB
	if path == ":memory:" {
		db.SetMaxOpenConns(1)
	}

	// Initialize schema
	if _, err := db.Exec(SchemaSQL); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to initialize schema: %w", err)
	}

	return &CacheClient{
		db:   db,
		path: path,
	}, nil
}

// Get retrieves the value for a key.
//
// Returns nil if the key doesn't exist. The returned byte slice should not be modified.
//
// Example:
//
//	value, err := client.Get("mykey")
//	if err != nil {
//		return err
//	}
//	if value == nil {
//		fmt.Println("Key not found")
//	}
func (c *CacheClient) Get(key string) ([]byte, error) {
	return _getCurrentValue(c.db, key)
}

// Set stores a value for a key.
//
// If the key already exists, a new version is created and the old value is
// soft-deleted (marked inactive but preserved for version history).
//
// Example:
//
//	err := client.Set("mykey", []byte("myvalue"))
func (c *CacheClient) Set(key string, value []byte) error {
	return _setValue(c.db, key, value)
}

// Delete removes a key (soft delete - marks as inactive).
//
// The value remains in the database for version history but is no longer
// accessible through Get or ListKeys.
//
// Example:
//
//	err := client.Delete("mykey")
func (c *CacheClient) Delete(key string) error {
	return _deleteKey(c.db, key)
}

// ListKeys returns all active keys, ordered by insertion time (newest first).
//
// Example:
//
//	keys, err := client.ListKeys()
//	if err != nil {
//		return err
//	}
//	for _, key := range keys {
//		fmt.Println(key)
//	}
func (c *CacheClient) ListKeys() ([]string, error) {
	return _listActiveKeys(c.db)
}

// Close closes the database connection.
//
// After calling Close, the client should not be used.
func (c *CacheClient) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.db != nil {
		err := c.db.Close()
		c.db = nil
		return err
	}
	return nil
}

// Path returns the database file path used by this client.
func (c *CacheClient) Path() string {
	return c.path
}
