from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .data_models import TABLE_SCHEMAS, normalize_dataframe, today_text


@dataclass(frozen=True)
class ImpactRule:
    keyword: str
    impact_area: str
    required_check: str
    alarm_level: str


IMPACT_RULES: list[ImpactRule] = [
    ImpactRule("Core Size", "Inductance, Isat, Core Loss, Temperature", "Electrical Spec, Thermal, Inspection Point", "High"),
    ImpactRule("Gap", "Inductance, DC Bias, Isat", "L Spec, DC Bias Curve, Inspection Standard", "High"),
    ImpactRule("Turn", "Inductance, DCR, Copper Loss, Temperature", "Electrical Spec, Winding Drawing, BOM", "High"),
    ImpactRule("Wire", "DCR, Current Density, Temperature, Winding Space", "DCR, Temperature, BOM, Winding Space", "High"),
    ImpactRule("Bobbin Material", "Hi-Pot, Insulation, ES/MS, Reliability", "ESMS, Hi-Pot, Material Approval", "High"),
    ImpactRule("Resin", "Temperature, Insulation, Reliability", "Thermal, Reliability, Process", "Medium"),
    ImpactRule("Terminal Position", "PCB Assembly, Customer Housing, Fastening", "PCB Hole, CMM Position, Customer Assembly", "High"),
    ImpactRule("Assy Size", "Customer Housing, Assembly Interference", "3D Interference, Inspection Standard, Customer Review", "High"),
    ImpactRule("BOM", "Approval, PPAP, Purchase, Drawing BOM", "BOM, Approval, PPAP Document", "Medium"),
    ImpactRule("Note", "Inspection, Manufacturing, Customer Requirement", "Drawing Note, Inspection Standard", "Medium"),
    ImpactRule("L_Assy", "Customer Housing, Assembly Interference", "3D Interference, Inspection Standard, Customer Review", "High"),
    ImpactRule("POS", "PCB Assembly, JIG, Position Inspection", "PCB Hole, CMM Position, Customer Assembly", "High"),
    ImpactRule("FLAT", "Seating Stability, Solder Quality", "Flatness Inspection, CMM Program", "High"),
    ImpactRule("DCR", "Copper Loss, Temperature, Efficiency", "Electrical Spec, Wire, Thermal", "High"),
    ImpactRule("Hi-Pot", "Insulation, Clearance, Reliability", "ESMS, Hi-Pot, Material Approval", "High"),
]


def match_impact_rule(changed_item: str = "", changed_symbol: str = "") -> ImpactRule:
    haystack = f"{changed_item} {changed_symbol}".lower()
    for rule in IMPACT_RULES:
        if rule.keyword.lower() in haystack:
            return rule
    return ImpactRule("Default", "Related drawing/spec/process", "Manual engineering review", "Medium")


def build_impact_row(rev: str, changed_item: str, changed_symbol: str, before: object, after: object, owner: str = "") -> dict[str, object]:
    rule = match_impact_rule(changed_item, changed_symbol)
    return {
        "Rev": rev,
        "Changed Item": changed_item,
        "Changed Symbol": changed_symbol,
        "Before": before,
        "After": after,
        "Impact Area": rule.impact_area,
        "Required Check": rule.required_check,
        "Alarm Level": rule.alarm_level,
        "Owner": owner,
        "Due Date": "",
        "Status": "Open",
        "Comment": f"{changed_item or changed_symbol} 변경 영향 검토 필요",
    }


def generate_revision_impact(change_history_df: pd.DataFrame) -> pd.DataFrame:
    history = normalize_dataframe(change_history_df, "change_history")
    rows = []
    for _, row in history.iterrows():
        rows.append(
            build_impact_row(
                row.get("Rev", ""),
                row.get("Changed Item", ""),
                row.get("Changed Symbol", ""),
                row.get("Before", ""),
                row.get("After", ""),
                row.get("User", ""),
            )
        )
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["revision_impact"])


def generate_inspection_revision_impact(
    revision_impact_df: pd.DataFrame,
    inspection_df: pd.DataFrame,
    measurement_df: pd.DataFrame,
) -> pd.DataFrame:
    impacts = normalize_dataframe(revision_impact_df, "revision_impact")
    inspections = normalize_dataframe(inspection_df, "inspection_standard_db")
    measurements = normalize_dataframe(measurement_df, "measurement_result_db")
    rows = []
    for _, impact in impacts.iterrows():
        symbol = str(impact.get("Changed Symbol", "")).strip()
        item = str(impact.get("Changed Item", "")).strip()
        keywords = ["Assy Size", "Terminal Position", "Hole", "Flatness", "Height", "Width", "Length"]
        related = inspections[
            (inspections["Confirmed"].astype(str).str.upper() == "Y")
            & (
                inspections["Symbol"].astype(str).str.contains(symbol, case=False, na=False)
                if symbol
                else inspections["Item"].astype(str).str.contains("|".join(keywords), case=False, na=False)
            )
        ]
        if related.empty and any(keyword.lower() in item.lower() for keyword in keywords):
            related = inspections[
                (inspections["Confirmed"].astype(str).str.upper() == "Y")
                & inspections["Item"].astype(str).str.contains(item, case=False, na=False)
            ]
        for _, standard in related.iterrows():
            inspection_no = str(standard.get("No.", ""))
            has_measurement = not measurements[measurements["Inspection No."].astype(str) == inspection_no].empty
            rows.append(
                {
                    "Changed Item": item,
                    "Changed Symbol": symbol,
                    "Related Inspection No.": inspection_no,
                    "Related Measurement Data": "Y" if has_measurement else "N",
                    "Old Spec": impact.get("Before", ""),
                    "New Spec": impact.get("After", ""),
                    "Measurement Method": standard.get("Method", ""),
                    "Required Action": "검사 기준서 및 기존 측정 DATA 재평가 필요" if has_measurement else "검사 기준서 영향 검토 필요",
                    "Alarm Level": impact.get("Alarm Level", "Medium"),
                    "Owner": impact.get("Owner", ""),
                    "Status": "Open",
                    "Comment": f"Generated {today_text()}",
                }
            )
    return pd.DataFrame(rows, columns=TABLE_SCHEMAS["inspection_revision_impact"])
