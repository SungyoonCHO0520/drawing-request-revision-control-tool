from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.database import append_rows, create_project, load_project, replace_table, save_project
from src.excel_exporter import export_dataframes_to_excel, export_project_to_excel
from src.excel_importer import import_excel_to_project
from src.impact_rules import generate_inspection_revision_impact, generate_revision_impact
from src.inspection_pdf_parser import parse_inspection_pdf
from src.measurement_checker import check_measurement_results
from src.revision_compare import compare_projects
from src.sample_data import sample_project_data
from src.validators import validate_project


def cmd_create_project(args) -> None:
    create_project(args.output)
    print(f"Created project: {args.output}")


def cmd_create_sample(args) -> None:
    create_project(args.output, sample=True)
    print(f"Created sample project: {args.output}")


def cmd_export_excel(args) -> None:
    export_project_to_excel(args.project, args.output)
    print(f"Exported Excel: {args.output}")


def cmd_import_excel(args) -> None:
    warnings = import_excel_to_project(args.input, args.output)
    print(f"Imported Excel to project: {args.output}")
    for warning in warnings:
        print(f"WARNING: {warning}")


def cmd_validate(args) -> None:
    issues = validate_project(load_project(args.project))
    if issues.empty:
        print("Validation PASS: no issues")
    else:
        print(issues.to_string(index=False))


def cmd_compare(args) -> None:
    result = compare_projects(args.old, args.new, rev=Path(args.new).stem)
    dataframes = sample_project_data()
    dataframes["change_history"] = result["change_history"]
    dataframes["revision_impact"] = result["revision_impact"]
    export_dataframes_to_excel(dataframes, args.output)
    print(f"Revision compare exported: {args.output}")


def cmd_parse_inspection(args) -> None:
    raw_df, draft_df = parse_inspection_pdf(args.pdf)
    append_rows(args.project, "raw_ocr_text", raw_df.to_dict("records"))
    append_rows(args.project, "inspection_standard_db", draft_df.to_dict("records"))
    print(f"Parsed inspection PDF: raw={len(raw_df)}, candidates={len(draft_df)}")


def cmd_check_measurement(args) -> None:
    data = load_project(args.project)
    checked = check_measurement_results(data["measurement_result_db"], data["inspection_standard_db"])
    replace_table(args.project, "measurement_result_db", checked)
    print("Measurement data checked.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PFC IN Drawing Request & Revision Control Tool CLI")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("create-project")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_create_project)

    p = sub.add_parser("create-sample")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_create_sample)

    p = sub.add_parser("export-excel")
    p.add_argument("--project", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_export_excel)

    p = sub.add_parser("import-excel")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_import_excel)

    p = sub.add_parser("validate")
    p.add_argument("--project", required=True)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("compare")
    p.add_argument("--old", required=True)
    p.add_argument("--new", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("parse-inspection")
    p.add_argument("--project", required=True)
    p.add_argument("--pdf", required=True)
    p.set_defaults(func=cmd_parse_inspection)

    p = sub.add_parser("check-measurement")
    p.add_argument("--project", required=True)
    p.set_defaults(func=cmd_check_measurement)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
