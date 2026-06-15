from __future__ import annotations

import pandas as pd

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
