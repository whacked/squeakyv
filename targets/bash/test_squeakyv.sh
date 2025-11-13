#!/usr/bin/env bash
# Quick smoke test for squeakyv bash library

set -euo pipefail

# Source the library
source "$(dirname "$0")/squeakyv.sh"

echo "✓ Library sourced successfully"

# Use temp database
DB=$(mktemp /tmp/squeakyv_test.XXXXXX.db)
trap "rm -f $DB" EXIT

echo ""
echo "--- Test 1: Initialize database ---"
squeakyv_init_db "$DB"
echo "✓ Database initialized: $DB"

echo ""
echo "--- Test 2: Set values ---"
squeakyv_set_value "$DB" "key1" "value1"
squeakyv_set_value "$DB" "key2" "value2"
squeakyv_set_value "$DB" "key3" "value3"
echo "✓ Set 3 key-value pairs"

echo ""
echo "--- Test 3: Get value ---"
result=$(squeakyv_get_current_value "$DB" "key1")
if [[ "$result" == "value1" ]]; then
    echo "✓ Get key1: $result"
else
    echo "✗ Expected 'value1', got '$result'"
    exit 1
fi

echo ""
echo "--- Test 4: List keys ---"
keys=$(squeakyv_list_active_keys "$DB")
echo "Active keys:"
echo "$keys"
if echo "$keys" | grep -q "key1" && echo "$keys" | grep -q "key2" && echo "$keys" | grep -q "key3"; then
    echo "✓ All keys found"
else
    echo "✗ Not all keys found"
    exit 1
fi

echo ""
echo "--- Test 5: Update value ---"
squeakyv_set_value "$DB" "key1" "updated_value"
result=$(squeakyv_get_current_value "$DB" "key1")
if [[ "$result" == "updated_value" ]]; then
    echo "✓ Updated key1: $result"
else
    echo "✗ Expected 'updated_value', got '$result'"
    exit 1
fi

echo ""
echo "--- Test 6: Delete key ---"
squeakyv_delete_key "$DB" "key1"
result=$(squeakyv_get_current_value "$DB" "key1" || echo "")
if [[ -z "$result" ]]; then
    echo "✓ key1 deleted successfully (empty result)"
else
    echo "✗ Expected empty result after delete, got '$result'"
    exit 1
fi

echo ""
echo "--- Test 7: Verify key1 not in list ---"
keys=$(squeakyv_list_active_keys "$DB")
if ! echo "$keys" | grep -q "key1"; then
    echo "✓ key1 not in active keys list"
else
    echo "✗ key1 still in list after delete"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ All tests passed!"
echo "=================================================="
