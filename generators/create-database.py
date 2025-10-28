import os.path as _p
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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


# --- Type Mappings and Constants ---

# Dictionary mapping standard JSON Schema types to common SQLite affinities
SQLITE_TYPE_MAP = {
    "string": "TEXT",
    "integer": "INTEGER",
    "number": "REAL",
    "boolean": "INTEGER",  # SQLite often uses INTEGER for boolean (0 or 1)
    "array": "TEXT",  # Arrays usually serialized to JSON string in SQLite
    "object": "TEXT",  # Objects usually serialized to JSON string in SQLite
}

# --- Core DDL Logic ---


def map_json_type_to_sqlite(json_type: str) -> str:
    """Maps a JSON Schema type string to a SQLite affinity."""
    # Use .get() to default to TEXT if an unknown type appears
    return SQLITE_TYPE_MAP.get(json_type.lower(), "TEXT")


def generate_column_constraints(
    col_name: str,
    col_def: Dict[str, Any],
    required_list: List[str],
) -> str:
    """Generates the column-level constraints (NOT NULL, PRIMARY KEY, AUTOINCREMENT)."""
    constraints = []

    # 1. NOT NULL constraint (based on parent schema's 'required' array)
    if col_name in required_list:
        constraints.append("NOT NULL")

    # 2. PRIMARY KEY and AUTOINCREMENT
    if col_def.get("sqlite:primaryKey") is True:
        # SQLite best practice: INTEGER PRIMARY KEY implies AUTOINCREMENT (if specified)
        # Note: Your schema doesn't explicitly use AUTOINCREMENT, but it is a common
        # convention for single integer PKEYs in SQLite. We will use the explicit PKEY.

        # Check if it should be AUTOINCREMENT (e.g., explicit type integer for ID)
        if (
            map_json_type_to_sqlite(col_def.get("type", "")) == "INTEGER"
            and "id" in col_name.lower()
        ):
            # Using the column name 'id' as a heuristic for auto-increment.
            constraints.append("PRIMARY KEY AUTOINCREMENT")
        else:
            constraints.append("PRIMARY KEY")

    # 3. DEFAULT value (use raw SQL expression when provided)
    if "sqlite:default" in col_def:
        default_expr = col_def["sqlite:default"]
        constraints.append(f"DEFAULT ({default_expr})")

    # 4. CHECK constraint (raw SQL condition)
    if "sqlite:check" in col_def:
        check_expr = col_def["sqlite:check"]
        constraints.append(f"CHECK ({check_expr})")

    return " ".join(constraints)


def generate_create_table_ddl(table_name: str, table_schema: Dict[str, Any]) -> str:
    """
    Generates the full CREATE TABLE DDL for a single table schema definition,
    including table and column descriptions as comments.
    """

    # The actual table definition is nested under 'items' in your structure
    table_definition = table_schema.get("items", {})

    if not table_definition.get("properties"):
        return f"-- WARNING: Skipping table {table_name}: No properties defined in 'items'.\n"

    column_definitions = []
    foreign_key_constraints = []

    properties = table_definition["properties"]
    required_list = table_definition.get("required", [])

    # 1. Iterate through properties to build column definitions and collect FKEYs
    for col_name, col_def in properties.items():
        # Allow explicit SQLite type override via custom property
        sql_type = col_def.get("sqlite:type") or map_json_type_to_sqlite(
            col_def.get("type", "string")
        )
        constraints = generate_column_constraints(col_name, col_def, required_list)

        col_ddl = ""

        # Add column description comment (preceding the column definition line)
        col_desc = col_def.get("description")
        if col_desc:
            # Replace newlines in description for a cleaner DDL comment
            clean_desc = col_desc.replace("\n", " ").strip()
            col_ddl += f"  -- {clean_desc}\n"

        # Add the actual column definition line
        col_ddl += f"  {col_name} {sql_type} {constraints}".rstrip()

        column_definitions.append(col_ddl)

        # 2. Check for and collect FOREIGN KEY definitions
        fkey_target = col_def.get("sqlite:foreignKey")
        if fkey_target:
            # The custom property is structured as 'table(column)', so we extract that
            if "(" in fkey_target and ")" in fkey_target:
                ref_table, ref_col_paren = fkey_target.split("(", 1)
                ref_col = ref_col_paren.rstrip(")")

                # Append the constraint definition
                foreign_key_constraints.append(
                    f"  FOREIGN KEY({col_name}) REFERENCES {ref_table.strip()}({ref_col.strip()})"
                )
            else:
                # Note: In a production environment, this should log to a file or stream
                pass

    # 3. Assemble the final DDL statement
    ddl = ""
    # Add Table Description (Multi-line comment)
    table_desc = table_schema.get("description")
    if table_desc:
        ddl += f"/*\n * Table: {table_name}\n * Description: {table_desc}\n */\n"

    ddl_parts = column_definitions + foreign_key_constraints
    ddl += f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    ddl += ",\n".join(ddl_parts)
    ddl += "\n);\n"

    return ddl


def generate_metadata_inserts(
    metadata_table_name: str, schema_version: str, schema_tree_ish: str
) -> str:
    """
    Generates the idempotent INSERT OR IGNORE statements for initial library metadata.

    In a real system, schema_version and schema_tree_ish would be calculated
    by reading the environment or the source schema file.
    """

    # We use INSERT OR IGNORE to ensure these are only run once
    inserts = [
        "\n/*",
        " * Initialization Data: Schema Version and Creation Date (Idempotent)",
        " * These records are only inserted if they do not already exist.",
        " */",
        f"INSERT OR IGNORE INTO {metadata_table_name} (key, value) VALUES ('schema_version', '{schema_version}');",
        f"INSERT OR IGNORE INTO {metadata_table_name} (key, value) VALUES ('schema_tree_ish', '{schema_tree_ish}');",
        # Use SQLite function for the current timestamp
        f"INSERT OR IGNORE INTO {metadata_table_name} (key, value) VALUES ('creation_date', strftime('%Y-%m-%dT%H:%M:%f', 'now'));",
    ]
    return "\n".join(inserts)


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


def generate_kv_constraints(kv_info: KVTableInfo) -> str:
    """
    Generates indexes and triggers for the key-value table based on schema info.
    """
    # Generate constraint names based on table name
    active_index_name = f"{kv_info.table_name}_active_{kv_info.key_field}"
    time_index_name = f"{kv_info.table_name}_{kv_info.key_field}_time"
    trigger_name = f"{kv_info.table_name}_swap_active"

    return f"""
-- Only one active row per key
CREATE UNIQUE INDEX {active_index_name} ON {kv_info.table_name}({kv_info.key_field}) WHERE {kv_info.is_active_field} = 1;

-- Time-travel and scans
CREATE INDEX {time_index_name} ON {kv_info.table_name}({kv_info.key_field}, {kv_info.inserted_at_field});

-- Swap-out on overwrite: retire old active row just before insert
CREATE TRIGGER {trigger_name}
BEFORE INSERT ON {kv_info.table_name}
FOR EACH ROW
BEGIN
  UPDATE {kv_info.table_name} SET {kv_info.is_active_field} = 0
  WHERE {kv_info.key_field} = NEW.{kv_info.key_field} AND {kv_info.is_active_field} = 1;
END;

-- Convenience view
CREATE VIEW IF NOT EXISTS {kv_info.table_name}_current AS
  SELECT {kv_info.key_field}, {kv_info.value_field}, {kv_info.inserted_at_field}
  FROM {kv_info.table_name}
  WHERE {kv_info.is_active_field} = 1;
"""


def generate_table_ddl(master_schema: Dict[str, Any]) -> List[str]:
    """
    Main entry point. Iterates through the top-level table schemas and generates DDL
    and appends initialization data.
    """
    ddl_statements = []

    # Track if we generated the metadata table DDL
    metadata_table_name: Optional[str] = None

    # 1. Loop over all tables to generate CREATE TABLE statements
    for table_name, table_schema in master_schema.items():
        # Check if the schema looks like a table definition (type 'array' with 'items')
        if table_schema.get("type") == "array" and "items" in table_schema:
            try:
                ddl = generate_create_table_ddl(table_name, table_schema)
                ddl_statements.append(ddl)

                if table_name == "__metadata__":
                    metadata_table_name = table_name
            except Exception as e:
                ddl_statements.append(f"-- ERROR generating DDL for {table_name}: {e}")
        else:
            ddl_statements.append(
                f"-- Skipping {table_name}: Not a recognized table structure."
            )

    # 2. Append Initialization Data if the metadata table was defined
    if metadata_table_name is not None:
        # NOTE: In a real system, you would calculate these values from your build/environment.
        # We use placeholders here to demonstrate the injection logic.
        VERSION = "1.0.0"
        TREE_ISH = (
            "git-hash-abc123"  # e.g., git rev-parse HEAD or hash of the jsonnet file
        )

        insert_statements = generate_metadata_inserts(
            metadata_table_name, VERSION, TREE_ISH
        )
        ddl_statements.append(insert_statements)

    return ddl_statements


if __name__ == "__main__":
    json_schema_path = sys.argv[1]
    assert json_schema_path.endswith(".json")
    assert _p.exists(json_schema_path)

    with open(json_schema_path) as ifile:
        json_schema = jsonref.load(ifile)

    for statement in generate_table_ddl(json_schema["properties"]):
        print(statement)

    kv_info = find_kv_table_info(json_schema["properties"])
    if kv_info:
        print(generate_kv_constraints(kv_info))
    else:
        print("-- WARNING: No KV table found in schema, skipping constraints")
