from __future__ import annotations

from src.database import append_rows, create_project, load_project, save_project
from src.data_models import TABLE_SCHEMAS


def test_sqlite_project_creation_and_raw_ocr_save(tmp_path):
    project = tmp_path / "sample.pfcproj"
    create_project(project, sample=True)

    data = load_project(project)
    assert set(TABLE_SCHEMAS) == set(data)
    assert not data["electrical_spec"].empty

    append_rows(
        project,
        "raw_ocr_text",
        [{"Source File": "inspection.pdf", "Page": 1, "Extracted Text": "105.1±0.6", "OCR Used": "N", "Confidence": "1.0", "Confirmed": "N", "Remark": ""}],
    )
    reloaded = load_project(project)
    assert "105.1±0.6" in reloaded["raw_ocr_text"]["Extracted Text"].tolist()


def test_save_project_preserves_added_table_columns(tmp_path):
    project = tmp_path / "sample.pfcproj"
    create_project(project, sample=True)
    data = load_project(project)
    data["electrical_spec"]["User Added Column"] = "saved"

    save_project(project, data)
    reloaded = load_project(project)

    assert "User Added Column" in reloaded["electrical_spec"].columns
    assert reloaded["electrical_spec"].loc[0, "User Added Column"] == "saved"
