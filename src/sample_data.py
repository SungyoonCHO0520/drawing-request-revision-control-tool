from __future__ import annotations

import pandas as pd

from .data_models import TABLE_SCHEMAS, empty_dataframe, normalize_dataframe, today_text


def drawing_request_summary_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Project": "PFC IN 개발",
                "Product": "HE ICCU OBC PFC IN ASSY",
                "Customer": "Internal / Customer TBD",
                "Request Rev": "A",
                "Request Date": today_text(),
                "Requester": "Development Team",
                "Target Drawing Rev": "A",
                "Request Purpose": "기구팀 도면 작성 요청 및 전기/신뢰성/Note 기입 정보 전달",
                "Mechanical Team Request": "전기적 특성표, ES/MS, BOM, Note, 검사 기준 반영",
                "Key Risk": "PCB 조립성, 절연거리, DCR, Hi-Pot",
                "Required Review Department": "개발팀, 기구팀, 품질팀, 생산팀",
                "Due Date": "",
                "Remark": "샘플 프로젝트",
            }
        ],
        columns=TABLE_SCHEMAS["drawing_request_summary"],
    )


def electrical_spec_df() -> pd.DataFrame:
    rows = [
        [1, "Inductance", "L", "100kHz, 0.1V", "", 530, "", "uH", "L = 530uH ±10%", "Y", "Core, Gap, Turn", "Spec Table", "High", ""],
        [2, "DCR", "Rdc", "25℃", "", "", 18, "mΩ", "Rdc ≤ 18mΩ", "Y", "Wire, Turn", "Spec Table", "High", ""],
        [3, "Hi-Pot", "ACW", "5 sec", "", 2.5, "", "kVac", "AC 2.5kV, 5sec", "Y", "Bobbin, Clearance", "Spec Table", "High", ""],
        [4, "Insulation Resistance", "IR", "DC 500V", 100, "", "", "MΩ", "IR ≥ 100MΩ", "Y", "Bobbin, Resin", "Spec Table", "High", ""],
    ]
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["electrical_spec"])


def reliability_df() -> pd.DataFrame:
    items = [
        "High Temperature Storage",
        "Low Temperature Storage",
        "Thermal Shock",
        "Temperature Humidity",
        "Vibration",
        "Mechanical Shock",
        "Solder Heat",
        "Insulation Resistance",
        "Hi-Pot",
    ]
    rows = []
    for index, item in enumerate(items, start=1):
        rows.append(
            {
                "No.": index,
                "Test Item": item,
                "Standard": "Customer / ES-MS",
                "Condition": "TBD" if index <= 3 else "",
                "Sample Qty": "",
                "Judgment": "",
                "Drawing Text": "",
                "Required": "Y",
                "Related Item": item,
                "Change Risk": "High" if item in {"Insulation Resistance", "Hi-Pot"} else "Medium",
                "Remark": "",
            }
        )
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["reliability"])


def esms_df() -> pd.DataFrame:
    rows = [
        [1, "ES/MS", "Material", "Flame retardant requirement", "Bobbin", "PET-GF30 V0", "Material Certificate", "Y", "Bobbin", "High", ""],
        [2, "ES/MS", "Insulation", "Required clearance/creepage", "Bobbin, Coil", "To be checked", "Drawing, Test Report", "Y", "Hi-Pot", "High", ""],
    ]
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["esms"])


def bom_df() -> pd.DataFrame:
    rows = [
        [1, "Core", "Sendust", "TBD", "TBD", 1, 1, "L, Isat, Core Loss", "High", "Core Assembly", ""],
        [2, "Bobbin", "PET-GF30", "V0", "TBD", 1, 2, "Hi-Pot, ES/MS", "High", "Injection", ""],
        [3, "Coil", "Cu Wire", "TBD", "TBD", 1, 3, "DCR, Temperature", "High", "Winding", ""],
        [4, "Terminal", "Cu Alloy", "TBD", "TBD", 3, 4, "PCB Fastening", "Medium", "Assembly", ""],
        [5, "Resin", "Epoxy", "TBD", "TBD", 1, 5, "Thermal, Insulation", "Medium", "Potting", ""],
    ]
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["bom"])


def note_df() -> pd.DataFrame:
    categories = ["Insulation", "Soldering", "Measurement", "Assembly", "Appearance", "Customer Requirement"]
    rows = []
    for index, category in enumerate(categories, start=1):
        rows.append([index, category, "", "Y", "Note", category, "Medium", "필수 Note 문구 확인 필요"])
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["note"])


def inspection_standard_df() -> pd.DataFrame:
    rows = [
        [1, "1", "제품 전체 길이", "제품 전체 길이", "L_Assy_Total", "Top View", "A,B", 105.1, 105.7, 104.5, "mm", "Direct Measurement", "Vernier or CMM", 5, "Critical", "Customer Housing Interference", 1, "105.1±0.6", "Y", ""],
        [2, "5", "M3 Nut 위치도", "M3 Nut 위치도", "POS_M3Nut_Btm", "Top View", "A,B,D", 0.2, 0.2, "", "mm", "Coordinate Measurement", "CMM", 5, "Critical", "PCB Fastening", 1, "Ø0.2 | A | B | D", "Y", ""],
        [3, "10", "실제 안착면 평면도", "실제 안착면 평면도", "FLAT_Seat", "Side View", "A", 0.25, 0.25, "", "mm", "Flatness Measurement", "CMM", 5, "Major", "Seating Stability", 1, "0.25", "Y", ""],
    ]
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["inspection_standard_db"])


def measurement_result_df() -> pd.DataFrame:
    rows = [
        ["L2501", today_text(), "A", "A", "A", 1, 1, "제품 전체 길이", "L_Assy_Total", 105.1, 105.7, 104.5, 105.2, "mm", "", "Vernier", "Inspector A", ""],
        ["L2501", today_text(), "A", "A", "A", 1, 2, "M3 Nut 위치도", "POS_M3Nut_Btm", 0.2, 0.2, "", 0.18, "mm", "", "CMM", "Inspector A", ""],
    ]
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["measurement_result_db"])


def empty_review_checklist_df() -> pd.DataFrame:
    return empty_dataframe("drawing_review_checklist")


def empty_revision_impact_df() -> pd.DataFrame:
    return empty_dataframe("revision_impact")


def empty_inspection_revision_impact_df() -> pd.DataFrame:
    return empty_dataframe("inspection_revision_impact")


def empty_change_history_df() -> pd.DataFrame:
    return empty_dataframe("change_history")


def empty_raw_ocr_df() -> pd.DataFrame:
    return empty_dataframe("raw_ocr_text")


def sample_project_data() -> dict[str, pd.DataFrame]:
    data = {
        "drawing_request_summary": drawing_request_summary_df(),
        "electrical_spec": electrical_spec_df(),
        "reliability": reliability_df(),
        "esms": esms_df(),
        "bom": bom_df(),
        "note": note_df(),
        "drawing_review_checklist": empty_review_checklist_df(),
        "inspection_standard_db": inspection_standard_df(),
        "measurement_result_db": measurement_result_df(),
        "revision_impact": empty_revision_impact_df(),
        "inspection_revision_impact": empty_inspection_revision_impact_df(),
        "change_history": empty_change_history_df(),
        "raw_ocr_text": empty_raw_ocr_df(),
    }
    return {table: normalize_dataframe(frame, table) for table, frame in data.items()}
