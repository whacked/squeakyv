import sqlite3

DEBUG_LEVEL = 0


def delete_key(conn: sqlite3.Connection, key) -> None:
    """Execute delete_key query, returns None"""
    statement = """UPDATE kv
SET is_active = 0
WHERE key = :key AND is_active = 1;
"""
    parameters = {"key": key}
    if DEBUG_LEVEL > 0:
        print("STATEMENT:", statement)
        print("PARAMETERS:", parameters)
    cursor = conn.execute(statement, parameters)

    return None


def get_current_value(conn: sqlite3.Connection, key) -> str | bytes:
    """Execute get_current_value query, returns str | bytes"""
    statement = """SELECT value -- , inserted_at
FROM kv
WHERE key = :key AND is_active = 1;
"""
    parameters = {"key": key}
    if DEBUG_LEVEL > 0:
        print("STATEMENT:", statement)
        print("PARAMETERS:", parameters)
    cursor = conn.execute(statement, parameters)

    return cursor.fetchone()[0]


def list_active_keys(conn: sqlite3.Connection, ) -> list[str | bytes]:
    """Execute list_active_keys query, returns list[str | bytes]"""
    statement = """SELECT key -- , inserted_at
FROM kv
WHERE is_active = 1
ORDER BY inserted_at DESC;
"""
    parameters = {}
    if DEBUG_LEVEL > 0:
        print("STATEMENT:", statement)
        print("PARAMETERS:", parameters)
    cursor = conn.execute(statement, parameters)

    return [row[0] for row in cursor.fetchall()]


def set_value(conn: sqlite3.Connection, key, value) -> None:
    """Execute set_value query, returns None"""
    statement = """INSERT INTO kv (key, value)
VALUES (:key, :value);
"""
    parameters = {"key": key, "value": value}
    if DEBUG_LEVEL > 0:
        print("STATEMENT:", statement)
        print("PARAMETERS:", parameters)
    cursor = conn.execute(statement, parameters)

    return None
