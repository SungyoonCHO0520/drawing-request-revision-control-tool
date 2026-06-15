from __future__ import annotations

from pathlib import Path

import pandas as pd

from .data_models import TABLE_SCHEMAS, normalize_dataframe, today_text
from .database import load_project
from .impact_rules import generate_revision_impact


COMPARE_TABLES = ["electrical_spec", "reliability", "esms", "bom", "note", "inspection_standard_db"]
KEY_CANDIDATES = ["Symbol", "Item No.", "No.", "Item", "Test Item", "Category"]


def _row_key(row: pd.Series) -> str:
    for column in KEY_CANDIDATES:
        value = str(row.get(column, "")).strip()
        if value:
            return f"{column}:{value}"
    return "|".join(str(value) for value in row.tolist())


def _symbol_for_row(row: pd.Series) -> str:
    for column in ["Symbol", "Item No.", "No."]:
        value = str(row.get(column, "")).strip()
        if value:
            return value
    return ""


def _item_for_row(row: pd.Series) -> str:
    for column in ["Item", "Part Name", "Test Item", "Requirement", "Category", "Inspection Point"]:
        value = str(row.get(column, "")).strip()
        if value:
            return value
    return ""


def compare_table(old_df: pd.DataFrame, new_df: pd.DataFrame, table_name: str, rev: str = "") -> pd.DataFrame:
    old_df = normalize_dataframe(old_df, table_name)
    new_df = normalize_dataframe(new_df, table_name)
    old_map = {_row_key(row): row for _, row in old_df.iterrows()}
    new_map = {_row_key(row): row for _, row in new_df.iterrows()}
    rows: list[dict[str, object]] = []
    for key in sorted(set(old_map) | set(new_map)):
        old_row = old_map.get(key)
        new_row = new_map.get(key)
        if old_row is None:
            item = _item_for_row(new_row)
            symbol = _symbol_for_row(new_row)
            before = ""
            after = new_row.to_dict()
            reason = "Added"
        elif new_row is None:
            item = _item_for_row(old_row)
            symbol = _symbol_for_row(old_row)
            before = old_row.to_dict()
            after = ""
            reason = "Deleted"
        elif old_row.astype(str).to_dict() != new_row.astype(str).to_dict():
            item = _item_for_row(new_row)
            symbol = _symbol_for_row(new_row)
            before = old_row.to_dict()
            after = new_row.to_dict()
            reason = "Changed"
        else:
            continue
        rows.append(
            {
                "Date": today_text(),
                "User": "",
                "Rev": rev,
                "Changed Sheet": table_name,
                "Changed Item": item,
                "Changed Symbol": symbol,
                "Before": str(before),
                "After": str(after),
                "Reason": reason,
                "Impact Summary": "Revision 영향도 자동 생성 대상",
                "Comment": key,
            }
        )
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["change_history"])


def compare_dataframes(old_data: dict[str, pd.DataFrame], new_data: dict[str, pd.DataFrame], rev: str = "") -> dict[str, pd.DataFrame]:
    changes = []
    for table_name in COMPARE_TABLES:
        table_changes = compare_table(old_data.get(table_name), new_data.get(table_name), table_name, rev)
        if not table_changes.empty:
            changes.append(table_changes)
    change_history = pd.concat(changes, ignore_index=True) if changes else pd.DataFrame(columns=TABLE_SCHEMAS["change_history"])
    revision_impact = generate_revision_impact(change_history)
    return {
        "change_history": change_history,
        "revision_impact": revision_impact,
    }


def compare_projects(old_project: str | Path, new_project: str | Path, rev: str = "") -> dict[str, pd.DataFrame]:
    return compare_dataframes(load_project(old_project), load_project(new_project), rev)
