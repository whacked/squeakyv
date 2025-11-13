#!/usr/bin/env bash
# Demo script showing squeakyv bash usage

source "$(dirname "$0")/squeakyv.sh"

echo "=== squeakyv Bash Demo ==="
echo ""

# Temporary database
DB=$(mktemp /tmp/squeakyv_demo.XXXXXX.db)
trap "rm -f $DB; echo 'Cleaned up $DB'" EXIT

echo "1. Initialize database: $DB"
squeakyv_init_db "$DB"
echo ""

echo "2. Store some configuration values"
squeakyv_set_value "$DB" "app_name" "squeakyv-demo"
squeakyv_set_value "$DB" "version" "0.1.0"
squeakyv_set_value "$DB" "debug_mode" "true"
echo "   ✓ Stored 3 config values"
echo ""

echo "3. Retrieve a value"
app_name=$(squeakyv_get_current_value "$DB" "app_name")
echo "   app_name = $app_name"
echo ""

echo "4. List all keys"
echo "   Active keys:"
squeakyv_list_active_keys "$DB" | sed 's/^/     - /'
echo ""

echo "5. Update a value (creates new version)"
squeakyv_set_value "$DB" "version" "0.2.0"
new_version=$(squeakyv_get_current_value "$DB" "version")
echo "   Updated version: $new_version"
echo ""

echo "6. Delete a key"
squeakyv_delete_key "$DB" "debug_mode"
echo "   ✓ Deleted debug_mode"
echo ""

echo "7. Check deleted key returns empty"
result=$(squeakyv_get_current_value "$DB" "debug_mode")
if [[ -z "$result" ]]; then
    echo "   ✓ debug_mode returns empty (deleted)"
else
    echo "   ✗ Unexpected value: $result"
fi
echo ""

echo "8. Final key list"
squeakyv_list_active_keys "$DB" | sed 's/^/     - /'
echo ""

echo "=== Demo Complete ==="
