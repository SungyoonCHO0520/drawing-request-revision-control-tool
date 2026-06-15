from __future__ import annotations

from collections import OrderedDict
from datetime import date
from typing import Iterable

import pandas as pd


TOOL_NAME = "Drawing Request & Revision Control Tool"
PROJECT_EXTENSION = ".pfcproj"
DEFAULT_PROJECT_NAME = "PFC IN Project"
PROJECT_ID_COLUMN = "_project_id"

YES_NO_OPTIONS = ["Y", "N"]
RESULT_OPTIONS = ["PASS", "NG", "CHECK", "MISSING"]
ALARM_LEVEL_OPTIONS = ["High", "Medium", "Low"]
STATUS_OPTIONS = ["Open", "In Progress", "Done", "Hold"]
CHANGE_RISK_OPTIONS = ["High", "Medium", "Low"]

TABLE_SCHEMAS: "OrderedDict[str, list[str]]" = OrderedDict(
    {
        "drawing_request_summary": [
            "Project",
            "Product",
            "Customer",
            "Request Rev",
            "Request Date",
            "Requester",
            "Target Drawing Rev",
            "Request Purpose",
            "Mechanical Team Request",
            "Key Risk",
            "Required Review Department",
            "Due Date",
            "Remark",
        ],
        "electrical_spec": [
            "No.",
            "Item",
            "Symbol",
            "Condition",
            "Min",
            "Typ",
            "Max",
            "Unit",
            "Drawing Text",
            "Critical",
            "Related Item",
            "Related Drawing Area",
            "Change Risk",
            "Remark",
        ],
        "reliability": [
            "No.",
            "Test Item",
            "Standard",
            "Condition",
            "Sample Qty",
            "Judgment",
            "Drawing Text",
            "Required",
            "Related Item",
            "Change Risk",
            "Remark",
        ],
        "esms": [
            "No.",
            "Customer Spec",
            "Clause",
            "Requirement",
            "Applied Part",
            "Drawing Text",
            "Evidence",
            "Required",
            "Related Item",
            "Change Risk",
            "Remark",
        ],
        "bom": [
            "Item No.",
            "Part Name",
            "Material",
            "Spec",
            "Maker",
            "Qty",
            "Drawing Balloon",
            "Related Spec",
            "Change Risk",
            "Related Process",
            "Remark",
        ],
        "note": [
            "No.",
            "Category",
            "Note Text",
            "Required",
            "Drawing Area",
            "Related Risk",
            "Change Risk",
            "Remark",
        ],
        "drawing_review_checklist": [
            "No.",
            "Check Item",
            "Source Sheet",
            "Expected",
            "Drawing Actual",
            "Result",
            "Alarm Level",
            "Owner",
            "Comment",
        ],
        "inspection_standard_db": [
            "No.",
            "Drawing No.",
            "Inspection Point",
            "Item",
            "Symbol",
            "View",
            "Datum",
            "Nominal",
            "Upper",
            "Lower",
            "Unit",
            "Method",
            "Tool",
            "Sample Qty",
            "Criticality",
            "Related Risk",
            "Source PDF Page",
            "Source Text",
            "Confirmed",
            "Remark",
        ],
        "measurement_result_db": [
            "Lot",
            "Date",
            "Product Rev",
            "Drawing Rev",
            "Inspection Standard Rev",
            "Sample No.",
            "Inspection No.",
            "Item",
            "Symbol",
            "Nominal",
            "Upper",
            "Lower",
            "Measured Value",
            "Unit",
            "Result",
            "Tool",
            "Inspector",
            "Remark",
        ],
        "revision_impact": [
            "Rev",
            "Changed Item",
            "Changed Symbol",
            "Before",
            "After",
            "Impact Area",
            "Required Check",
            "Alarm Level",
            "Owner",
            "Due Date",
            "Status",
            "Comment",
        ],
        "inspection_revision_impact": [
            "Changed Item",
            "Changed Symbol",
            "Related Inspection No.",
            "Related Measurement Data",
            "Old Spec",
            "New Spec",
            "Measurement Method",
            "Required Action",
            "Alarm Level",
            "Owner",
            "Status",
            "Comment",
        ],
        "change_history": [
            "Date",
            "User",
            "Rev",
            "Changed Sheet",
            "Changed Item",
            "Changed Symbol",
            "Before",
            "After",
            "Reason",
            "Impact Summary",
            "Comment",
        ],
        "raw_ocr_text": [
            "Source File",
            "Page",
            "Extracted Text",
            "OCR Used",
            "Confidence",
            "Confirmed",
            "Remark",
        ],
    }
)

SHEET_NAMES: dict[str, str] = {
    "drawing_request_summary": "Drawing_Request_Summary",
    "electrical_spec": "Electrical_Spec",
    "reliability": "Reliability",
    "esms": "ESMS",
    "bom": "BOM",
    "note": "Note",
    "drawing_review_checklist": "Drawing_Review_Checklist",
    "inspection_standard_db": "Inspection_Standard_DB",
    "measurement_result_db": "Measurement_Result_DB",
    "revision_impact": "Revision_Impact",
    "inspection_revision_impact": "Inspection_Revision_Impact",
    "change_history": "Change_History",
    "raw_ocr_text": "Raw_OCR_Text",
}

SHEET_TO_TABLE = {sheet: table for table, sheet in SHEET_NAMES.items()}

MODULE_LABELS: dict[str, str] = {
    "drawing_request_summary": "Summary",
    "electrical_spec": "Electrical Spec",
    "reliability": "Reliability",
    "esms": "ESMS",
    "bom": "BOM",
    "note": "Note",
    "drawing_review_checklist": "Drawing Review Checklist",
    "inspection_standard_db": "Inspection Standard DB",
    "measurement_result_db": "Measurement Result DB",
    "revision_impact": "Revision Impact",
    "inspection_revision_impact": "Inspection Revision Impact",
    "change_history": "Change History",
    "raw_ocr_text": "Raw OCR Text",
}

LABEL_TO_TABLE = {label: table for table, label in MODULE_LABELS.items()}
MODULE_KEY_TO_TABLE: dict[str, str] = {
    "summary": "drawing_request_summary",
    "electrical_spec": "electrical_spec",
    "reliability": "reliability",
    "esms": "esms",
    "bom": "bom",
    "note": "note",
    "drawing_review_checklist": "drawing_review_checklist",
    "inspection_standard_db": "inspection_standard_db",
    "measurement_result_db": "measurement_result_db",
    "revision_impact": "revision_impact",
    "inspection_revision_impact": "inspection_revision_impact",
    "change_history": "change_history",
    "raw_ocr_text": "raw_ocr_text",
}
TABLE_TO_MODULE_KEY = {table: key for key, table in MODULE_KEY_TO_TABLE.items()}
DEFAULT_MODULE_DISPLAY_NAMES = {
    module_key: MODULE_LABELS[table_name]
    for module_key, table_name in MODULE_KEY_TO_TABLE.items()
}

DROPDOWN_COLUMNS: dict[str, list[str]] = {
    "Critical": YES_NO_OPTIONS,
    "Required": YES_NO_OPTIONS,
    "Confirmed": YES_NO_OPTIONS,
    "Result": RESULT_OPTIONS,
    "Alarm Level": ALARM_LEVEL_OPTIONS,
    "Status": STATUS_OPTIONS,
    "Change Risk": CHANGE_RISK_OPTIONS,
}

VALIDATION_COLUMNS = [
    "Sheet",
    "Row",
    "Item",
    "Symbol",
    "Result",
    "Alarm Level",
    "Message",
    "Required Action",
]


def empty_dataframe(table_name: str) -> pd.DataFrame:
    return pd.DataFrame(columns=TABLE_SCHEMAS[table_name])


def normalize_dataframe(df: pd.DataFrame | None, table_name: str, keep_extra: bool = True) -> pd.DataFrame:
    columns = TABLE_SCHEMAS[table_name]
    if df is None:
        return empty_dataframe(table_name)
    normalized = df.copy()
    for column in columns:
        if column not in normalized.columns:
            normalized[column] = ""
    ordered_columns = columns.copy()
    if keep_extra:
        ordered_columns.extend([column for column in normalized.columns if column not in ordered_columns])
    return normalized[ordered_columns].fillna("")


def normalize_all(dataframes: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {table: normalize_dataframe(dataframes.get(table), table) for table in TABLE_SCHEMAS}


def today_text() -> str:
    return date.today().isoformat()


def first_nonblank(values: Iterable[object]) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""
