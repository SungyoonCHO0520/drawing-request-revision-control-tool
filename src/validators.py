from __future__ import annotations

import pandas as pd

from .data_models import VALIDATION_COLUMNS, normalize_dataframe
from .measurement_checker import check_measurement_results


def _is_blank(value: object) -> bool:
    return str(value or "").strip() == ""


def _is_tbd(value: object) -> bool:
    return str(value or "").strip().upper() == "TBD"


def _issue(sheet: str, row: int, item: object, symbol: object, result: str, alarm: str, message: str, action: str) -> dict[str, object]:
    return {
        "Sheet": sheet,
        "Row": row,
        "Item": item,
        "Symbol": symbol,
        "Result": result,
        "Alarm Level": alarm,
        "Message": message,
        "Required Action": action,
    }


def generate_review_checklist(dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    electrical = normalize_dataframe(dataframes.get("electrical_spec"), "electrical_spec")
    for _, row in electrical[electrical["Critical"].astype(str).str.upper() == "Y"].iterrows():
        rows.append(
            {
                "No.": len(rows) + 1,
                "Check Item": row.get("Item", ""),
                "Source Sheet": "Electrical_Spec",
                "Expected": row.get("Drawing Text", ""),
                "Drawing Actual": "",
                "Result": "CHECK",
                "Alarm Level": "High",
                "Owner": "Development / Mechanical",
                "Comment": "Critical electrical spec must be checked on drawing.",
            }
        )

    reliability = normalize_dataframe(dataframes.get("reliability"), "reliability")
    for _, row in reliability[reliability["Required"].astype(str).str.upper() == "Y"].iterrows():
        rows.append(
            {
                "No.": len(rows) + 1,
                "Check Item": row.get("Test Item", ""),
                "Source Sheet": "Reliability",
                "Expected": row.get("Drawing Text", "") or row.get("Condition", ""),
                "Drawing Actual": "",
                "Result": "CHECK",
                "Alarm Level": row.get("Change Risk", "Medium"),
                "Owner": "Development / Quality",
                "Comment": "Required reliability item must be checked.",
            }
        )

    esms = normalize_dataframe(dataframes.get("esms"), "esms")
    for _, row in esms[esms["Required"].astype(str).str.upper() == "Y"].iterrows():
        rows.append(
            {
                "No.": len(rows) + 1,
                "Check Item": row.get("Requirement", ""),
                "Source Sheet": "ESMS",
                "Expected": row.get("Drawing Text", ""),
                "Drawing Actual": "",
                "Result": "CHECK",
                "Alarm Level": row.get("Change Risk", "High"),
                "Owner": "Development / Quality",
                "Comment": "Required ES/MS item must be checked.",
            }
        )

    bom = normalize_dataframe(dataframes.get("bom"), "bom")
    for _, row in bom[bom["Change Risk"].astype(str) == "High"].iterrows():
        rows.append(
            {
                "No.": len(rows) + 1,
                "Check Item": row.get("Part Name", ""),
                "Source Sheet": "BOM",
                "Expected": f"{row.get('Material', '')} / {row.get('Spec', '')}",
                "Drawing Actual": "",
                "Result": "CHECK",
                "Alarm Level": "High",
                "Owner": "Development / Mechanical / Purchase",
                "Comment": "High-risk BOM item must be checked.",
            }
        )

    note = normalize_dataframe(dataframes.get("note"), "note")
    for _, row in note[note["Required"].astype(str).str.upper() == "Y"].iterrows():
        rows.append(
            {
                "No.": len(rows) + 1,
                "Check Item": row.get("Category", ""),
                "Source Sheet": "Note",
                "Expected": row.get("Note Text", ""),
                "Drawing Actual": "",
                "Result": "CHECK",
                "Alarm Level": row.get("Change Risk", "Medium"),
                "Owner": "Development / Mechanical",
                "Comment": "Required Note must be checked.",
            }
        )

    return pd.DataFrame(rows, columns=[
        "No.",
        "Check Item",
        "Source Sheet",
        "Expected",
        "Drawing Actual",
        "Result",
        "Alarm Level",
        "Owner",
        "Comment",
    ])


def validate_project(dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    issues: list[dict[str, object]] = []

    electrical = normalize_dataframe(dataframes.get("electrical_spec"), "electrical_spec")
    for index, row in electrical.iterrows():
        if str(row.get("Critical", "")).upper() == "Y" and _is_blank(row.get("Drawing Text")):
            issues.append(_issue("Electrical_Spec", index + 2, row.get("Item"), row.get("Symbol"), "MISSING", "High", "Critical=Y 항목의 Drawing Text가 비어 있습니다.", "도면 기입 문구 작성 필요"))

    reliability = normalize_dataframe(dataframes.get("reliability"), "reliability")
    for index, row in reliability.iterrows():
        if str(row.get("Required", "")).upper() == "Y" and _is_blank(row.get("Condition")):
            issues.append(_issue("Reliability", index + 2, row.get("Test Item"), "", "MISSING", "Medium", "Required=Y 신뢰성 항목의 Condition이 비어 있습니다.", "시험 조건 입력 필요"))

    esms = normalize_dataframe(dataframes.get("esms"), "esms")
    for index, row in esms.iterrows():
        if str(row.get("Required", "")).upper() == "Y" and _is_blank(row.get("Evidence")):
            issues.append(_issue("ESMS", index + 2, row.get("Requirement"), "", "CHECK", "Medium", "Required=Y ES/MS 항목의 Evidence가 비어 있습니다.", "근거 자료 확인 필요"))

    bom = normalize_dataframe(dataframes.get("bom"), "bom")
    for index, row in bom.iterrows():
        if str(row.get("Change Risk", "")) == "High" and (_is_blank(row.get("Spec")) or _is_tbd(row.get("Spec"))):
            issues.append(_issue("BOM", index + 2, row.get("Part Name"), "", "CHECK", "High", "High Risk BOM의 Spec이 비어 있거나 TBD입니다.", "재질/사양 확정 필요"))

    note = normalize_dataframe(dataframes.get("note"), "note")
    for index, row in note.iterrows():
        if str(row.get("Required", "")).upper() == "Y" and _is_blank(row.get("Note Text")):
            issues.append(_issue("Note", index + 2, row.get("Category"), "", "MISSING", "Medium", "Required=Y Note의 문구가 비어 있습니다.", "도면 Note 문구 작성 필요"))

    inspection = normalize_dataframe(dataframes.get("inspection_standard_db"), "inspection_standard_db")
    for index, row in inspection.iterrows():
        if str(row.get("Criticality", "")) == "Critical" and str(row.get("Confirmed", "")).upper() != "Y":
            issues.append(_issue("Inspection_Standard_DB", index + 2, row.get("Item"), row.get("Symbol"), "CHECK", "High", "Critical 검사 항목이 Confirmed=Y가 아닙니다.", "사람 검토 후 Confirmed=Y 승인 필요"))

    measurement = check_measurement_results(dataframes.get("measurement_result_db"), inspection)
    for index, row in measurement.iterrows():
        if row.get("Result") in {"NG", "MISSING", "CHECK"}:
            issues.append(_issue("Measurement_Result_DB", index + 2, row.get("Item"), row.get("Symbol"), row.get("Result"), "High" if row.get("Result") == "NG" else "Medium", "측정 DATA 판정 확인 필요", "측정값/기준값 재확인"))

    revision = normalize_dataframe(dataframes.get("revision_impact"), "revision_impact")
    for index, row in revision.iterrows():
        if str(row.get("Alarm Level", "")) == "High" and (_is_blank(row.get("Owner")) or _is_blank(row.get("Status"))):
            issues.append(_issue("Revision_Impact", index + 2, row.get("Changed Item"), row.get("Changed Symbol"), "CHECK", "High", "High 알람인데 Owner 또는 Status가 비어 있습니다.", "담당자와 진행 상태 입력 필요"))

    return pd.DataFrame(issues, columns=VALIDATION_COLUMNS)
