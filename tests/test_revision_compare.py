from __future__ import annotations

from src.revision_compare import compare_dataframes
from src.sample_data import sample_project_data


def test_revision_compare_result_generation():
    old = sample_project_data()
    new = sample_project_data()
    new["electrical_spec"].loc[0, "Typ"] = "540"

    result = compare_dataframes(old, new, rev="B")

    assert not result["change_history"].empty
    assert not result["revision_impact"].empty
    assert result["change_history"].iloc[0]["Changed Sheet"] == "electrical_spec"
