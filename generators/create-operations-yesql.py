import json
import sys
import os.path as _p
from dataclasses import dataclass
from typing import Any, Dict, Optional

import jinja2  # type: ignore
import jsonref  # type: ignore

# --- Data Classes ---


@dataclass
class KVTableInfo:
    """Information about a key-value table extracted from schema."""

    table_name: str
    key_field: str
    value_field: str
    inserted_at_field: str
    is_active_field: str


# --- PYTHON LOOKUP LOGIC ---


def find_kv_table_info(master_schema: Dict[str, Any]) -> Optional[KVTableInfo]:
    """
    Finds the key-value table using hydrated JSON Schema (jsonref-resolved).
    Detects by presence of expected KV fields inside items.properties.
    """
    for table_name, table_schema in master_schema.items():
        if table_schema.get("type") == "array" and isinstance(
            table_schema.get("items"), dict
        ):
            items_obj = table_schema["items"]
            properties = items_obj.get("properties") or {}
            if not isinstance(properties, dict):
                continue

            prop_names = set(properties.keys())
            # Minimal required fields for our KV table
            if {"key", "value", "inserted_at", "is_active"}.issubset(prop_names):
                return KVTableInfo(
                    table_name=table_name,
                    key_field="key",
                    value_field="value",
                    inserted_at_field="inserted_at",
                    is_active_field="is_active",
                )
    return None


# We embed the Jinja2 template string directly for convenience.
# The template is now much cleaner, relying on pre-resolved variables.
J2_TEMPLATE = jinja2.Template("""\
{# This file uses Jinja2 syntax to generate the final YeSQL file dynamically. #}

-- ====================================================================
-- Auto-generated Key-Value Access Queries (Single Table with Active Flag)
-- Table: {{ kv_info.table_name }}
-- ====================================================================

-- name: get-current-value(key)^
-- Retrieves the current active value for a key
SELECT {{ kv_info.value_field }}, {{ kv_info.inserted_at_field }}
FROM {{ kv_info.table_name }}
WHERE {{ kv_info.key_field }} = :key AND {{ kv_info.is_active_field }} = 1;

-- name: set-value(key, value)*
-- Sets a new value for a key (trigger handles deactivating old values)
INSERT INTO {{ kv_info.table_name }} ({{ kv_info.key_field }}, {{ kv_info.value_field }})
VALUES (:key, :value)
RETURNING {{ kv_info.key_field }}, {{ kv_info.value_field }}, {{ kv_info.inserted_at_field }};

-- name: delete-key(key)!
-- Soft deletes a key by setting is_active = 0
UPDATE {{ kv_info.table_name }}
SET {{ kv_info.is_active_field }} = 0
WHERE {{ kv_info.key_field }} = :key AND {{ kv_info.is_active_field }} = 1;

-- name: list-active-keys()^
-- Lists all currently active keys
SELECT {{ kv_info.key_field }}, {{ kv_info.inserted_at_field }}
FROM {{ kv_info.table_name }}
WHERE {{ kv_info.is_active_field }} = 1
ORDER BY {{ kv_info.inserted_at_field }} DESC;
""")


if __name__ == "__main__":
    json_schema_path = sys.argv[1]
    assert json_schema_path.endswith(".json")
    assert _p.exists(json_schema_path)

    with open(json_schema_path) as ifile:
        json_schema_dict = jsonref.load(ifile)

    kv_info = find_kv_table_info(json_schema_dict.get("properties", {}))
    if not kv_info:
        print("ERROR: No KV table found in schema", file=sys.stderr)
        sys.exit(1)

    print(J2_TEMPLATE.render(kv_info=kv_info))
