package squeakyv

import (
	"bytes"
	"fmt"
	"path/filepath"
	"sync"
	"testing"
)

func TestNewCacheClient(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	if client.Path() != ":memory:" {
		t.Errorf("Expected path :memory:, got %s", client.Path())
	}
}

func TestSetAndGet(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	// Set a value
	key := "testkey"
	value := []byte("testvalue")

	err = client.Set(key, value)
	if err != nil {
		t.Fatalf("Failed to set value: %v", err)
	}

	// Get the value
	retrieved, err := client.Get(key)
	if err != nil {
		t.Fatalf("Failed to get value: %v", err)
	}

	if !bytes.Equal(retrieved, value) {
		t.Errorf("Expected %s, got %s", value, retrieved)
	}
}

func TestGetNonExistent(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	value, err := client.Get("nonexistent")
	if err != nil {
		t.Fatalf("Failed to get value: %v", err)
	}

	if value != nil {
		t.Errorf("Expected nil for nonexistent key, got %v", value)
	}
}

func TestUpdate(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	key := "testkey"

	// Set initial value
	err = client.Set(key, []byte("value1"))
	if err != nil {
		t.Fatalf("Failed to set initial value: %v", err)
	}

	// Update value
	err = client.Set(key, []byte("value2"))
	if err != nil {
		t.Fatalf("Failed to update value: %v", err)
	}

	// Verify updated value
	value, err := client.Get(key)
	if err != nil {
		t.Fatalf("Failed to get value: %v", err)
	}

	expected := []byte("value2")
	if !bytes.Equal(value, expected) {
		t.Errorf("Expected %s, got %s", expected, value)
	}
}

func TestDelete(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	key := "testkey"
	value := []byte("testvalue")

	// Set value
	err = client.Set(key, value)
	if err != nil {
		t.Fatalf("Failed to set value: %v", err)
	}

	// Delete
	err = client.Delete(key)
	if err != nil {
		t.Fatalf("Failed to delete: %v", err)
	}

	// Verify deleted
	retrieved, err := client.Get(key)
	if err != nil {
		t.Fatalf("Failed to get value: %v", err)
	}

	if retrieved != nil {
		t.Errorf("Expected nil after delete, got %v", retrieved)
	}
}

func TestListKeys(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	// Set multiple values
	keys := []string{"key1", "key2", "key3"}
	for _, key := range keys {
		err = client.Set(key, []byte("value"))
		if err != nil {
			t.Fatalf("Failed to set %s: %v", key, err)
		}
	}

	// List keys
	retrieved, err := client.ListKeys()
	if err != nil {
		t.Fatalf("Failed to list keys: %v", err)
	}

	if len(retrieved) != len(keys) {
		t.Errorf("Expected %d keys, got %d", len(keys), len(retrieved))
	}

	// Check all keys are present
	keyMap := make(map[string]bool)
	for _, key := range retrieved {
		keyMap[key] = true
	}

	for _, key := range keys {
		if !keyMap[key] {
			t.Errorf("Key %s not found in list", key)
		}
	}
}

func TestListKeysAfterDelete(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	// Set multiple values
	client.Set("key1", []byte("value1"))
	client.Set("key2", []byte("value2"))
	client.Set("key3", []byte("value3"))

	// Delete one
	err = client.Delete("key2")
	if err != nil {
		t.Fatalf("Failed to delete: %v", err)
	}

	// List keys
	keys, err := client.ListKeys()
	if err != nil {
		t.Fatalf("Failed to list keys: %v", err)
	}

	// Should have 2 keys
	if len(keys) != 2 {
		t.Errorf("Expected 2 keys after delete, got %d", len(keys))
	}

	// key2 should not be in list
	for _, key := range keys {
		if key == "key2" {
			t.Error("Deleted key2 still in list")
		}
	}
}

func TestPersistence(t *testing.T) {
	// Create temp file
	tmpDir := t.TempDir()
	dbPath := filepath.Join(tmpDir, "test.db")

	// Create client and set value
	client1, err := NewCacheClient(dbPath)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	key := "persist_key"
	value := []byte("persist_value")
	err = client1.Set(key, value)
	if err != nil {
		t.Fatalf("Failed to set value: %v", err)
	}
	client1.Close()

	// Reopen and verify
	client2, err := NewCacheClient(dbPath)
	if err != nil {
		t.Fatalf("Failed to reopen database: %v", err)
	}
	defer client2.Close()

	retrieved, err := client2.Get(key)
	if err != nil {
		t.Fatalf("Failed to get value: %v", err)
	}

	if !bytes.Equal(retrieved, value) {
		t.Errorf("Expected %s, got %s", value, retrieved)
	}
}

func TestConcurrentAccess(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	var wg sync.WaitGroup
	numGoroutines := 10
	numOps := 100

	// Concurrent writes
	wg.Add(numGoroutines)
	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			defer wg.Done()
			for j := 0; j < numOps; j++ {
				key := fmt.Sprintf("key_%d_%d", id, j)
				value := []byte(fmt.Sprintf("value_%d_%d", id, j))
				if err := client.Set(key, value); err != nil {
					t.Errorf("Failed to set: %v", err)
				}
			}
		}(i)
	}

	wg.Wait()

	// Verify we have the expected number of keys
	keys, err := client.ListKeys()
	if err != nil {
		t.Fatalf("Failed to list keys: %v", err)
	}

	expected := numGoroutines * numOps
	if len(keys) != expected {
		t.Errorf("Expected %d keys, got %d", expected, len(keys))
	}
}

func TestBinaryData(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	// Binary data with null bytes
	binary := []byte{0x00, 0x01, 0x02, 0xFF, 0xFE, 0x00}

	err = client.Set("binary", binary)
	if err != nil {
		t.Fatalf("Failed to set binary data: %v", err)
	}

	retrieved, err := client.Get("binary")
	if err != nil {
		t.Fatalf("Failed to get binary data: %v", err)
	}

	if !bytes.Equal(retrieved, binary) {
		t.Errorf("Binary data mismatch")
	}
}

func TestEmptyValue(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	err = client.Set("empty", []byte{})
	if err != nil {
		t.Fatalf("Failed to set empty value: %v", err)
	}

	retrieved, err := client.Get("empty")
	if err != nil {
		t.Fatalf("Failed to get empty value: %v", err)
	}

	if len(retrieved) != 0 {
		t.Errorf("Expected empty slice, got %v", retrieved)
	}
}

func TestClose(t *testing.T) {
	client, err := NewCacheClient(":memory:")
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}

	err = client.Close()
	if err != nil {
		t.Errorf("Failed to close client: %v", err)
	}

	// Second close should not panic
	err = client.Close()
	if err != nil {
		t.Errorf("Second close failed: %v", err)
	}
}

// Example demonstrates basic usage of the squeakyv package.
func ExampleCacheClient() {
	// Create an in-memory cache
	client, err := NewCacheClient(":memory:")
	if err != nil {
		panic(err)
	}
	defer client.Close()

	// Store a value
	err = client.Set("mykey", []byte("myvalue"))
	if err != nil {
		panic(err)
	}

	// Retrieve a value
	value, err := client.Get("mykey")
	if err != nil {
		panic(err)
	}
	fmt.Println(string(value))

	// Output: myvalue
}
