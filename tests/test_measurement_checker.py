from __future__ import annotations

import pandas as pd

from src.measurement_checker import check_measurement_results, judge_measurement
from src.sample_data import inspection_standard_df, measurement_result_df


def test_measurement_upper_lower_pass_ng_missing_check():
    assert judge_measurement(5, 10, 1) == "PASS"
    assert judge_measurement(11, 10, 1) == "NG"
    assert judge_measurement("", 10, 1) == "MISSING"
    assert judge_measurement(5, "", "") == "CHECK"


def test_measurement_db_result_written():
    measurements = measurement_result_df()
    measurements.loc[0, "Measured Value"] = 999
    checked = check_measurement_results(measurements, inspection_standard_df())

    assert checked.loc[0, "Result"] == "NG"
    assert checked.loc[1, "Result"] == "PASS"
