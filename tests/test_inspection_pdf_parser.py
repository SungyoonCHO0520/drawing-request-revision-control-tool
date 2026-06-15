from __future__ import annotations

import pandas as pd

from src.database import append_rows, create_project, load_project
from src.inspection_pdf_parser import (
    parse_dimension_candidates,
    parse_dimension_spec,
    parse_inspection_standard_dimension_rows,
)


def _raw_df(text: str, page: int = 2) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Source File": "inspection.pdf",
                "Page": page,
                "Extracted Text": text,
                "OCR Used": "N",
                "Confidence": "1.0",
                "Confirmed": "N",
                "Remark": "",
            }
        ]
    )


def _sample_24_text() -> str:
    specs = [
        "105.10±0.6",
        "48.90±0.5",
        "69.11±0.5",
        "82.91±0.6",
        "Ø0.2",
        "Ø0.2",
        "Ø0.2",
        "Ø3.5±0.1",
        "Ø2.5±0.1",
        "Ø2.7+0.2/-0",
        "Ø0.2",
        "Ø0.2",
        "Ø0.2",
        "Ø3.5±0.1",
        "Ø0.2",
        "0.25",
        "min 11.5",
        "max 17.9",
        "min 100.5",
        "min 4.8",
        "MAX 32.0",
        "3.6±0.2",
        "12.0±0.3",
        "7.5±0.2",
    ]
    return "\n".join(f"1-{index} Dimension inspection standard {spec} Sample 5EA/Lot" for index, spec in enumerate(specs, start=1))


def test_dimension_candidate_regex_fallback_from_raw_text():
    raw = _raw_df("105.1±0.6 / 3-Ø3.5±0.1 / MAX 32.0 / Ø0.2 | A | B | D", page=1)

    candidates = parse_dimension_candidates(raw)

    assert len(candidates) >= 4
    assert set(candidates["Confirmed"]) == {"N"}


def test_parse_1_1_to_1_24_dimension_rows_from_page_text():
    candidates = parse_inspection_standard_dimension_rows(_raw_df(_sample_24_text()))

    assert len(candidates) == 24
    assert candidates["No."].tolist() == list(range(1, 25))
    assert candidates["Drawing No."].tolist()[0] == "1-1"
    assert candidates["Drawing No."].tolist()[-1] == "1-24"
    assert set(candidates["Item"]) == {"Dimension"}
    assert set(candidates["Confirmed"]) == {"N"}
    assert set(candidates["Source PDF Page"]) == {2}
    assert candidates.loc[0, "Symbol"] == "DIM_01"
    assert candidates.loc[23, "Symbol"] == "DIM_24"
    assert candidates.loc[0, "Sample Qty"] == "5EA/Lot"


def test_dimension_spec_parsing_rules():
    assert parse_dimension_spec("105.10±0.6") == {"nominal": 105.1, "upper": 105.7, "lower": 104.5, "unit": "mm", "symbol_type": "Dimension"}
    assert parse_dimension_spec("48.90±0.5")["upper"] == 49.4
    diameter = parse_dimension_spec("Ø3.5±0.1")
    assert diameter["symbol_type"] == "Diameter"
    assert diameter["nominal"] == 3.5
    assert diameter["upper"] == 3.6
    assert diameter["lower"] == 3.4
    position = parse_dimension_spec("Ø0.2")
    assert position["symbol_type"] == "Position"
    assert position["nominal"] == 0.2
    assert position["upper"] == 0.2
    assert position["lower"] == ""
    flatness = parse_dimension_spec("0.25", inspection_no=16)
    assert flatness["symbol_type"] == "Flatness"
    assert flatness["upper"] == 0.25
    assert flatness["lower"] == ""
    assert parse_dimension_spec("min 11.5")["lower"] == 11.5
    assert parse_dimension_spec("max 17.9")["upper"] == 17.9
    asymmetric = parse_dimension_spec("Ø2.7+0.2/-0")
    assert asymmetric["nominal"] == 2.7
    assert asymmetric["upper"] == 2.9
    assert asymmetric["lower"] == 2.7


def test_tool_method_mapping_and_draft_values_for_24_items():
    candidates = parse_inspection_standard_dimension_rows(_raw_df(_sample_24_text()))

    assert candidates.loc[0, "Method"] == "Distance"
    assert candidates.loc[0, "Tool"] == "V/C"
    assert candidates.loc[4, "Method"] == "Position"
    assert candidates.loc[4, "Tool"] == "GO-NO JIG"
    assert candidates.loc[7, "Method"] == "Diameter"
    assert candidates.loc[7, "Tool"] == "V/C"
    assert candidates.loc[15, "Method"] == "Flatness"
    assert candidates.loc[15, "Tool"] == "CMM"
    assert candidates.loc[20, "Method"] == "Distance"
    assert candidates.loc[20, "Tool"] == "JIG"
    assert candidates.loc[21, "Method"] == "Distance"
    assert candidates.loc[21, "Tool"] == "GO-NO JIG"
    assert candidates.loc[0, "Criticality"] == "Major"
    assert candidates.loc[0, "Remark"] == "Auto extracted from Inspection Standard PDF. Need human confirmation."


def test_inspection_standard_db_can_store_24_drafts(tmp_path):
    project = tmp_path / "sample.pfcproj"
    create_project(project)
    candidates = parse_inspection_standard_dimension_rows(_raw_df(_sample_24_text()))

    append_rows(project, "inspection_standard_db", candidates.to_dict("records"))
    data = load_project(project)

    assert len(data["inspection_standard_db"]) == 24
    assert data["inspection_standard_db"].loc[0, "Confirmed"] == "N"
