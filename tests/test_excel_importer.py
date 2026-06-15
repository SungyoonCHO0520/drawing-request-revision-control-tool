from __future__ import annotations

from src.database import create_project, load_project
from src.excel_exporter import export_project_to_excel
from src.excel_importer import import_excel_to_project


def test_import_excel_keeps_data(tmp_path):
    project = tmp_path / "sample.pfcproj"
    xlsx = tmp_path / "sample.xlsx"
    imported = tmp_path / "imported.pfcproj"
    create_project(project, sample=True)
    export_project_to_excel(project, xlsx)

    warnings = import_excel_to_project(xlsx, imported)
    data = load_project(imported)

    assert data["electrical_spec"].loc[0, "Item"] == "Inductance"
    assert isinstance(warnings, list)
