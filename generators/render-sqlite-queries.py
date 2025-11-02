#!/usr/bin/env python3
"""
Renders YeSQL queries as plain SQLite query templates for use with Python's sqlite library.
Reads from ./sql/database-operations.autogen.yesql.sql and outputs procedural SQL statements.
"""

import importlib
import os.path as _p
import sys
from pprint import pprint
from typing import Any, Dict

import aiosql
from aiosql.queries import Queries
from aiosql.types import QueryFn


def render_sqlite_queries(
    target_language: str, statements_map: Dict[str, QueryFn]
) -> None:
    # we need to import from language.<target-language>.py
    module_name = f"languages.{target_language}"
    module = importlib.import_module(module_name)
    rendered_code = module.render(statements_map).strip()
    print(rendered_code)

    return
    for k, v in statements_map.items():
        print("===", k, "===")
        print("OP", v.operation)
        print("ATTRS", v.attributes)
        print("SQL", v.sql)
        print("PARAMS", v.parameters)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            f"Usage: python3 {__file__} <target-language> <yesql-file-path>",
            file=sys.stderr,
        )
        sys.exit(1)

    target_language = sys.argv[1]
    yesql_file_path = sys.argv[2]

    queries: Queries = aiosql.from_path(yesql_file_path, "sqlite3")

    statements_map: Dict[str, QueryFn] = {}
    # pprint(statements_map)
    for k in queries.available_queries:
        if k.endswith("_cursor"):
            continue
        statements_map[k] = getattr(queries, k)
    render_sqlite_queries(target_language, statements_map)
