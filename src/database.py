from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

from .data_models import (
    DEFAULT_MODULE_DISPLAY_NAMES,
    DEFAULT_PROJECT_NAME,
    PROJECT_ID_COLUMN,
    TABLE_SCHEMAS,
    today_text,
    normalize_dataframe,
)


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def connect(project_path: str | Path) -> sqlite3.Connection:
    path = Path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    rows = connection.execute(f"PRAGMA table_info({quote_identifier(table_name)})").fetchall()
    return [row["name"] for row in rows]


def ensure_table(connection: sqlite3.Connection, table_name: str, columns: Iterable[str] | None = None) -> None:
    all_columns = list(TABLE_SCHEMAS[table_name] if columns is None else columns)
    column_sql = ", ".join(f"{quote_identifier(column)} TEXT" for column in all_columns)
    connection.execute(f"CREATE TABLE IF NOT EXISTS {quote_identifier(table_name)} ({column_sql})")
    existing = table_columns(connection, table_name)
    for column in all_columns:
        if column not in existing:
            connection.execute(f"ALTER TABLE {quote_identifier(table_name)} ADD COLUMN {quote_identifier(column)} TEXT")
    connection.commit()


def ensure_project_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            project_type TEXT,
            customer TEXT,
            product TEXT,
            created_at TEXT,
            updated_at TEXT,
            remark TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS module_display_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            module_key TEXT,
            display_name TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cell_styles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            table_name TEXT,
            row_index INTEGER,
            column_name TEXT,
            background_color TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS column_display_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            table_name TEXT,
            column_name TEXT,
            display_name TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    connection.commit()


def ensure_data_table(connection: sqlite3.Connection, table_name: str, columns: Iterable[str] | None = None) -> None:
    all_columns = list(TABLE_SCHEMAS[table_name] if columns is None else columns)
    if PROJECT_ID_COLUMN not in all_columns:
        all_columns.append(PROJECT_ID_COLUMN)
    ensure_table(connection, table_name, all_columns)


def ensure_module_display_names(connection: sqlite3.Connection, project_id: str | int) -> None:
    project_id = str(project_id)
    now = today_text()
    for module_key, display_name in DEFAULT_MODULE_DISPLAY_NAMES.items():
        row = connection.execute(
            "SELECT id FROM module_display_names WHERE project_id = ? AND module_key = ?",
            (project_id, module_key),
        ).fetchone()
        if row is None:
            connection.execute(
                """
                INSERT INTO module_display_names
                (project_id, module_key, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, module_key, display_name, now, now),
            )
    connection.commit()


def ensure_default_project(connection: sqlite3.Connection) -> str:
    ensure_project_tables(connection)
    row = connection.execute("SELECT id FROM projects ORDER BY id LIMIT 1").fetchone()
    if row is None:
        now = today_text()
        cursor = connection.execute(
            """
            INSERT INTO projects
            (project_name, project_type, customer, product, created_at, updated_at, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (DEFAULT_PROJECT_NAME, "Default", "", "", now, now, "Auto-created for backward compatibility"),
        )
        connection.commit()
        project_id = str(cursor.lastrowid)
    else:
        project_id = str(row["id"])
    ensure_module_display_names(connection, project_id)
    return project_id


def migrate_existing_rows_to_project(connection: sqlite3.Connection, project_id: str | int) -> None:
    project_id = str(project_id)
    for table_name in TABLE_SCHEMAS:
        ensure_data_table(connection, table_name)
        connection.execute(
            f"""
            UPDATE {quote_identifier(table_name)}
            SET {quote_identifier(PROJECT_ID_COLUMN)} = ?
            WHERE {quote_identifier(PROJECT_ID_COLUMN)} IS NULL
               OR {quote_identifier(PROJECT_ID_COLUMN)} = ''
            """,
            (project_id,),
        )
    connection.commit()


def initialize_database(project_path: str | Path) -> None:
    with connect(project_path) as connection:
        ensure_project_tables(connection)
        for table_name, columns in TABLE_SCHEMAS.items():
            ensure_data_table(connection, table_name, columns)
        default_project_id = ensure_default_project(connection)
        migrate_existing_rows_to_project(connection, default_project_id)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS project_meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        connection.commit()


def create_project(project_path: str | Path, sample: bool = False) -> None:
    initialize_database(project_path)
    if sample:
        from .sample_data import sample_project_data

        save_project(project_path, sample_project_data())


def list_projects(project_path: str | Path) -> list[dict[str, object]]:
    initialize_database(project_path)
    with connect(project_path) as connection:
        rows = connection.execute("SELECT * FROM projects ORDER BY id").fetchall()
        for row in rows:
            ensure_module_display_names(connection, row["id"])
        return [dict(row) for row in rows]


def default_project_id(project_path: str | Path) -> str:
    initialize_database(project_path)
    with connect(project_path) as connection:
        return ensure_default_project(connection)


def add_project_record(
    project_path: str | Path,
    project_name: str,
    project_type: str = "Custom",
    customer: str = "",
    product: str = "",
    remark: str = "",
) -> str:
    initialize_database(project_path)
    now = today_text()
    with connect(project_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO projects
            (project_name, project_type, customer, product, created_at, updated_at, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_name, project_type, customer, product, now, now, remark),
        )
        project_id = str(cursor.lastrowid)
        connection.commit()
        ensure_module_display_names(connection, project_id)
        return project_id


def rename_project(project_path: str | Path, project_id: str | int, new_name: str) -> None:
    initialize_database(project_path)
    with connect(project_path) as connection:
        connection.execute(
            "UPDATE projects SET project_name = ?, updated_at = ? WHERE id = ?",
            (new_name, today_text(), str(project_id)),
        )
        connection.commit()


def delete_project_record(project_path: str | Path, project_id: str | int) -> None:
    initialize_database(project_path)
    project_id = str(project_id)
    with connect(project_path) as connection:
        project_count = connection.execute("SELECT COUNT(*) AS count FROM projects").fetchone()["count"]
        if project_count <= 1:
            raise ValueError("Cannot delete the last project.")
        for table_name in TABLE_SCHEMAS:
            ensure_data_table(connection, table_name)
            connection.execute(
                f"DELETE FROM {quote_identifier(table_name)} WHERE {quote_identifier(PROJECT_ID_COLUMN)} = ?",
                (project_id,),
            )
        connection.execute("DELETE FROM module_display_names WHERE project_id = ?", (project_id,))
        connection.execute("DELETE FROM cell_styles WHERE project_id = ?", (project_id,))
        connection.execute("DELETE FROM column_display_names WHERE project_id = ?", (project_id,))
        connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        connection.commit()


def load_cell_styles(project_path: str | Path, project_id: str | int) -> dict[str, dict[tuple[int, str], str]]:
    initialize_database(project_path)
    with connect(project_path) as connection:
        rows = connection.execute(
            """
            SELECT table_name, row_index, column_name, background_color
            FROM cell_styles
            WHERE project_id = ?
            """,
            (str(project_id),),
        ).fetchall()
        styles: dict[str, dict[tuple[int, str], str]] = {}
        for row in rows:
            table_styles = styles.setdefault(str(row["table_name"]), {})
            table_styles[(int(row["row_index"]), str(row["column_name"]))] = str(row["background_color"])
        return styles


def save_cell_styles(
    project_path: str | Path,
    styles_by_table: dict[str, dict[tuple[int, str], str]],
    project_id: str | int,
) -> None:
    initialize_database(project_path)
    now = today_text()
    with connect(project_path) as connection:
        connection.execute("DELETE FROM cell_styles WHERE project_id = ?", (str(project_id),))
        rows = []
        for table_name, table_styles in styles_by_table.items():
            for (row_index, column_name), background_color in table_styles.items():
                if background_color:
                    rows.append(
                        (
                            str(project_id),
                            str(table_name),
                            int(row_index),
                            str(column_name),
                            str(background_color),
                            now,
                            now,
                        )
                    )
        if rows:
            connection.executemany(
                """
                INSERT INTO cell_styles
                (project_id, table_name, row_index, column_name, background_color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        connection.commit()


def load_column_display_names(project_path: str | Path, project_id: str | int) -> dict[str, dict[str, str]]:
    initialize_database(project_path)
    with connect(project_path) as connection:
        rows = connection.execute(
            """
            SELECT table_name, column_name, display_name
            FROM column_display_names
            WHERE project_id = ?
            """,
            (str(project_id),),
        ).fetchall()
        names: dict[str, dict[str, str]] = {}
        for row in rows:
            names.setdefault(str(row["table_name"]), {})[str(row["column_name"])] = str(row["display_name"])
        return names


def save_column_display_names(
    project_path: str | Path,
    names_by_table: dict[str, dict[str, str]],
    project_id: str | int,
) -> None:
    initialize_database(project_path)
    now = today_text()
    with connect(project_path) as connection:
        connection.execute("DELETE FROM column_display_names WHERE project_id = ?", (str(project_id),))
        rows = []
        for table_name, table_names in names_by_table.items():
            for column_name, display_name in table_names.items():
                if display_name and display_name != column_name:
                    rows.append(
                        (
                            str(project_id),
                            str(table_name),
                            str(column_name),
                            str(display_name),
                            now,
                            now,
                        )
                    )
        if rows:
            connection.executemany(
                """
                INSERT INTO column_display_names
                (project_id, table_name, column_name, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        connection.commit()


def list_module_display_names(project_path: str | Path, project_id: str | int) -> dict[str, str]:
    initialize_database(project_path)
    with connect(project_path) as connection:
        ensure_module_display_names(connection, project_id)
        rows = connection.execute(
            "SELECT module_key, display_name FROM module_display_names WHERE project_id = ?",
            (str(project_id),),
        ).fetchall()
        display_names = DEFAULT_MODULE_DISPLAY_NAMES.copy()
        display_names.update({row["module_key"]: row["display_name"] for row in rows})
        return display_names


def rename_module_display(project_path: str | Path, project_id: str | int, module_key: str, new_name: str) -> None:
    initialize_database(project_path)
    with connect(project_path) as connection:
        ensure_module_display_names(connection, project_id)
        connection.execute(
            """
            UPDATE module_display_names
            SET display_name = ?, updated_at = ?
            WHERE project_id = ? AND module_key = ?
            """,
            (new_name, today_text(), str(project_id), module_key),
        )
        connection.commit()


def save_table(connection: sqlite3.Connection, table_name: str, dataframe: pd.DataFrame, project_id: str | int | None = None) -> None:
    project_id = str(project_id or ensure_default_project(connection))
    dataframe = normalize_dataframe(dataframe, table_name)
    if PROJECT_ID_COLUMN in dataframe.columns:
        dataframe = dataframe.drop(columns=[PROJECT_ID_COLUMN])
    ensure_data_table(connection, table_name, dataframe.columns)
    connection.execute(
        f"DELETE FROM {quote_identifier(table_name)} WHERE {quote_identifier(PROJECT_ID_COLUMN)} = ?",
        (project_id,),
    )
    if dataframe.empty:
        connection.commit()
        return
    dataframe = dataframe.copy()
    dataframe[PROJECT_ID_COLUMN] = project_id
    columns = list(dataframe.columns)
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(quote_identifier(column) for column in columns)
    rows = dataframe.astype(str).fillna("").itertuples(index=False, name=None)
    connection.executemany(
        f"INSERT INTO {quote_identifier(table_name)} ({column_sql}) VALUES ({placeholders})",
        list(rows),
    )
    connection.commit()


def load_table(connection: sqlite3.Connection, table_name: str, project_id: str | int | None = None) -> pd.DataFrame:
    project_id = str(project_id or ensure_default_project(connection))
    ensure_data_table(connection, table_name)
    dataframe = pd.read_sql_query(
        f"SELECT * FROM {quote_identifier(table_name)} WHERE {quote_identifier(PROJECT_ID_COLUMN)} = ?",
        connection,
        params=(project_id,),
    )
    if PROJECT_ID_COLUMN in dataframe.columns:
        dataframe = dataframe.drop(columns=[PROJECT_ID_COLUMN])
    return normalize_dataframe(dataframe, table_name)


def save_project(project_path: str | Path, dataframes: dict[str, pd.DataFrame], project_id: str | int | None = None) -> None:
    initialize_database(project_path)
    with connect(project_path) as connection:
        project_id = project_id or ensure_default_project(connection)
        for table_name in TABLE_SCHEMAS:
            save_table(connection, table_name, dataframes.get(table_name, pd.DataFrame()), project_id)


def load_project(project_path: str | Path, project_id: str | int | None = None) -> dict[str, pd.DataFrame]:
    initialize_database(project_path)
    with connect(project_path) as connection:
        project_id = project_id or ensure_default_project(connection)
        return {table_name: load_table(connection, table_name, project_id) for table_name in TABLE_SCHEMAS}


def append_rows(project_path: str | Path, table_name: str, rows: list[dict[str, object]], project_id: str | int | None = None) -> None:
    if not rows:
        return
    initialize_database(project_path)
    with connect(project_path) as connection:
        project_id = project_id or ensure_default_project(connection)
        current = load_table(connection, table_name, project_id)
        incoming = normalize_dataframe(pd.DataFrame(rows), table_name)
        save_table(connection, table_name, pd.concat([current, incoming], ignore_index=True), project_id)


def replace_table(project_path: str | Path, table_name: str, dataframe: pd.DataFrame, project_id: str | int | None = None) -> None:
    initialize_database(project_path)
    with connect(project_path) as connection:
        project_id = project_id or ensure_default_project(connection)
        save_table(connection, table_name, dataframe, project_id)
