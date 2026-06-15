from __future__ import annotations

from src.sample_data import sample_project_data
from src.validators import validate_project


def test_electrical_required_text_missing_and_bom_tbd_check():
    data = sample_project_data()
    data["electrical_spec"].loc[0, "Drawing Text"] = ""
    data["bom"].loc[0, "Spec"] = "TBD"

    issues = validate_project(data)

    assert "Electrical_Spec" in issues["Sheet"].tolist()
    assert "BOM" in issues["Sheet"].tolist()
    assert "MISSING" in issues["Result"].tolist()
    assert "CHECK" in issues["Result"].tolist()


def test_inspection_confirmed_rule():
    data = sample_project_data()
    data["inspection_standard_db"].loc[0, "Confirmed"] = "N"

    issues = validate_project(data)

    assert not issues[
        (issues["Sheet"] == "Inspection_Standard_DB")
        & (issues["Result"] == "CHECK")
    ].empty
