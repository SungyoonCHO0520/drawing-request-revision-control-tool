from __future__ import annotations

from openpyxl import Workbook

from .data_models import SHEET_NAMES, TABLE_SCHEMAS, normalize_dataframe
from .excel_styles import apply_base_styles, apply_conditional_formatting, apply_data_validation


def build_workbook(dataframes: dict) -> Workbook:
    wb = Workbook()
    wb.remove(wb.active)
    for table_name, columns in TABLE_SCHEMAS.items():
        sheet_name = SHEET_NAMES[table_name]
        ws = wb.create_sheet(sheet_name)
        df = normalize_dataframe(dataframes.get(table_name), table_name)
        ws.append(list(df.columns))
        for row in df.itertuples(index=False, name=None):
            ws.append(list(row))
    apply_base_styles(wb)
    apply_conditional_formatting(wb)
    apply_data_validation(wb)
    return wb
