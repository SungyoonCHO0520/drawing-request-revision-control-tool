from __future__ import annotations

from pathlib import Path

from .database import list_projects, list_module_display_names, load_project
from .workbook_builder import build_workbook


def export_dataframes_to_excel(dataframes: dict, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = build_workbook(dataframes)
    workbook.save(output)


def export_project_to_excel(project_path: str | Path, output_path: str | Path, project_id: str | int | None = None) -> None:
    dataframes = load_project(project_path, project_id)
    if project_id is not None:
        projects = list_projects(project_path)
        selected = next((project for project in projects if str(project["id"]) == str(project_id)), None)
        if selected and not dataframes["drawing_request_summary"].empty:
            dataframes["drawing_request_summary"].loc[0, "Project"] = selected.get("project_name", "")
            module_names = list_module_display_names(project_path, project_id)
            dataframes["drawing_request_summary"].loc[0, "Remark"] = (
                str(dataframes["drawing_request_summary"].loc[0, "Remark"] or "")
                + " | Module display names: "
                + ", ".join(f"{key}={value}" for key, value in module_names.items())
            ).strip(" |")
    export_dataframes_to_excel(dataframes, output_path)
