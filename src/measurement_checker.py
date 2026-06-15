from __future__ import annotations

import pandas as pd

from .data_models import normalize_dataframe


def _to_float(value: object) -> float | None:
    text = "" if value is None else str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def judge_measurement(measured_value: object, upper: object = "", lower: object = "") -> str:
    measured = _to_float(measured_value)
    upper_value = _to_float(upper)
    lower_value = _to_float(lower)
    if measured is None:
        return "MISSING"
    if upper_value is None and lower_value is None:
        return "CHECK"
    if upper_value is not None and measured > upper_value:
        return "NG"
    if lower_value is not None and measured < lower_value:
        return "NG"
    return "PASS"


def check_measurement_results(measurement_df: pd.DataFrame, inspection_df: pd.DataFrame) -> pd.DataFrame:
    measurements = normalize_dataframe(measurement_df, "measurement_result_db")
    standards = normalize_dataframe(inspection_df, "inspection_standard_db")
    standard_by_no = {
        str(row.get("No.", "")).strip(): row
        for _, row in standards.iterrows()
        if str(row.get("No.", "")).strip()
    }
    for index, row in measurements.iterrows():
        inspection_no = str(row.get("Inspection No.", "")).strip()
        standard = standard_by_no.get(inspection_no)
        upper = row.get("Upper", "")
        lower = row.get("Lower", "")
        if standard is not None:
            for column in ["Item", "Symbol", "Nominal", "Upper", "Lower", "Unit", "Tool"]:
                if str(row.get(column, "")).strip() == "":
                    source_column = "Tool" if column == "Tool" else column
                    measurements.at[index, column] = standard.get(source_column, "")
            upper = measurements.at[index, "Upper"]
            lower = measurements.at[index, "Lower"]
        measurements.at[index, "Result"] = judge_measurement(row.get("Measured Value", ""), upper, lower)
    return measurements
