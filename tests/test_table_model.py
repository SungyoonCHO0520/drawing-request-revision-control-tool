from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt

from desktop.table_model import PandasTableModel


def test_insert_row_above_and_below_positions():
    model = PandasTableModel(pd.DataFrame([{"A": "top"}, {"A": "bottom"}]))

    model.insert_row(1)
    df = model.dataframe()

    assert df["A"].tolist() == ["top", "", "bottom"]


def test_insert_column_left_and_right_positions():
    model = PandasTableModel(pd.DataFrame([{"A": "1", "B": "2"}]))

    left_name = model.insert_column(1, "Inserted")
    right_name = model.insert_column(3, "Inserted")
    df = model.dataframe()

    assert left_name == "Inserted"
    assert right_name == "Inserted 2"
    assert df.columns.tolist() == ["A", "Inserted", "B", "Inserted 2"]


def test_delete_row_removes_only_target_row():
    model = PandasTableModel(pd.DataFrame([{"A": "keep"}, {"A": "remove"}, {"A": "keep2"}]))

    model.delete_row(1)

    assert model.dataframe()["A"].tolist() == ["keep", "keep2"]


def test_delete_column_removes_only_target_column():
    model = PandasTableModel(pd.DataFrame([{"A": "1", "B": "2", "C": "3"}]))

    deleted = model.delete_column(1)

    assert deleted == "B"
    assert model.dataframe().columns.tolist() == ["A", "C"]


def test_cell_color_can_be_applied_shifted_and_cleared():
    model = PandasTableModel(pd.DataFrame([{"A": "top"}, {"A": "bottom"}]))
    first_cell = model.index(0, 0)

    model.set_cell_color([first_cell], "#FFFF00")
    model.set_cell_text_color([first_cell], "#000000")

    assert model.cell_colors() == {(0, "A"): "#FFFF00"}
    assert model.cell_text_colors() == {(0, "A"): "#000000"}
    assert model.data(first_cell, Qt.BackgroundRole).name().upper() == "#FFFF00"
    assert model.data(first_cell, Qt.ForegroundRole).name().upper() == "#000000"

    model.insert_row(0)

    assert model.cell_colors() == {(1, "A"): "#FFFF00"}
    assert model.cell_text_colors() == {(1, "A"): "#000000"}

    shifted_cell = model.index(1, 0)
    model.clear_cell_color([shifted_cell])
    model.clear_cell_text_color([shifted_cell])

    assert model.cell_colors() == {}
    assert model.cell_text_colors() == {}


def test_column_header_can_be_renamed_without_changing_internal_column():
    model = PandasTableModel(pd.DataFrame([{"Customer Spec": "ES/MS"}]))

    previous, renamed = model.rename_header(0, "고객 사양")

    assert previous == "Customer Spec"
    assert renamed == "고객 사양"
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "고객 사양"
    assert model.internal_column_name(0) == "Customer Spec"
    assert model.dataframe().columns.tolist() == ["Customer Spec"]
    assert model.header_display_names() == {"Customer Spec": "고객 사양"}


def test_duplicate_or_blank_column_header_is_rejected():
    model = PandasTableModel(pd.DataFrame([{"A": "1", "B": "2"}]))

    try:
        model.rename_header(0, "B")
        assert False, "Duplicate header should fail"
    except ValueError:
        pass


def test_cell_edit_signal_contains_position_column_and_values():
    model = PandasTableModel(pd.DataFrame([{"Item": "Before"}]))
    edits = []
    model.cellEdited.connect(lambda row, column, previous, updated: edits.append((row, column, previous, updated)))

    model.setData(model.index(0, 0), "After", Qt.EditRole)

    assert edits == [(0, "Item", "Before", "After")]


def test_pasted_value_emits_cell_edit_signal():
    model = PandasTableModel(pd.DataFrame([{"Item": ""}]))
    edits = []
    model.cellEdited.connect(lambda row, column, previous, updated: edits.append((row, column, previous, updated)))

    model.set_value(0, 0, "Pasted")

    assert edits == [(0, "Item", "", "Pasted")]

    try:
        model.rename_header(0, "  ")
        assert False, "Blank header should fail"
    except ValueError:
        pass
