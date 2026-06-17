from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


class PandasTableModel(QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame, cell_colors: dict[tuple[int, str], str] | None = None):
        super().__init__()
        self._df = dataframe.copy().fillna("")
        self._cell_colors = dict(cell_colors or {})

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            return str(self._df.iat[index.row(), index.column()])
        if role == Qt.BackgroundRole:
            column_name = str(self._df.columns[index.column()])
            color = self._cell_colors.get((index.row(), column_name))
            if color:
                return QColor(color)
        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        self._df.iat[index.row(), index.column()] = "" if value is None else str(value)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)

    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    def cell_colors(self) -> dict[tuple[int, str], str]:
        return dict(self._cell_colors)

    def set_cell_color(self, indexes: list[QModelIndex], color: str) -> None:
        valid_indexes = [index for index in indexes if index.isValid()]
        if not valid_indexes:
            return
        for index in valid_indexes:
            column_name = str(self._df.columns[index.column()])
            self._cell_colors[(index.row(), column_name)] = color
        self._emit_background_changed(valid_indexes)

    def clear_cell_color(self, indexes: list[QModelIndex]) -> None:
        valid_indexes = [index for index in indexes if index.isValid()]
        if not valid_indexes:
            return
        for index in valid_indexes:
            column_name = str(self._df.columns[index.column()])
            self._cell_colors.pop((index.row(), column_name), None)
        self._emit_background_changed(valid_indexes)

    def _emit_background_changed(self, indexes: list[QModelIndex]) -> None:
        rows = [index.row() for index in indexes]
        columns = [index.column() for index in indexes]
        top_left = self.index(min(rows), min(columns))
        bottom_right = self.index(max(rows), max(columns))
        self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])

    def _shift_colors_for_insert_row(self, position: int) -> None:
        shifted = {}
        for (row, column_name), color in self._cell_colors.items():
            shifted[(row + 1 if row >= position else row, column_name)] = color
        self._cell_colors = shifted

    def _shift_colors_for_deleted_rows(self, rows: list[int]) -> None:
        removed = sorted(set(row for row in rows if 0 <= row < len(self._df)))
        if not removed:
            return
        shifted = {}
        for (row, column_name), color in self._cell_colors.items():
            if row in removed:
                continue
            shift = sum(1 for removed_row in removed if removed_row < row)
            shifted[(row - shift, column_name)] = color
        self._cell_colors = shifted

    def add_row(self) -> None:
        self.insert_row(len(self._df))

    def insert_row(self, position: int) -> None:
        position = max(0, min(position, len(self._df)))
        row = {column: "" for column in self._df.columns}
        self.beginInsertRows(QModelIndex(), position, position)
        self._shift_colors_for_insert_row(position)
        upper = self._df.iloc[:position]
        lower = self._df.iloc[position:]
        self._df = pd.concat([upper, pd.DataFrame([row]), lower], ignore_index=True)
        self.endInsertRows()

    def delete_rows(self, rows: list[int]) -> None:
        self._shift_colors_for_deleted_rows(rows)
        for row in sorted(set(rows), reverse=True):
            if row < 0 or row >= len(self._df):
                continue
            self.beginRemoveRows(QModelIndex(), row, row)
            self._df = self._df.drop(self._df.index[row]).reset_index(drop=True)
            self.endRemoveRows()

    def delete_row(self, row: int) -> None:
        self.delete_rows([row])

    def insert_column(self, position: int, name: str | None = None) -> str:
        position = max(0, min(position, len(self._df.columns)))
        column_name = self._unique_column_name(name or "New Column")
        self.beginInsertColumns(QModelIndex(), position, position)
        self._df.insert(position, column_name, "")
        self.endInsertColumns()
        return column_name

    def delete_column(self, column: int) -> str | None:
        if column < 0 or column >= len(self._df.columns):
            return None
        column_name = str(self._df.columns[column])
        self.beginRemoveColumns(QModelIndex(), column, column)
        self._df = self._df.drop(columns=[column_name])
        self._cell_colors = {
            (row, name): color
            for (row, name), color in self._cell_colors.items()
            if name != column_name
        }
        self.endRemoveColumns()
        return column_name

    def _unique_column_name(self, base_name: str) -> str:
        if base_name not in self._df.columns:
            return base_name
        suffix = 2
        while f"{base_name} {suffix}" in self._df.columns:
            suffix += 1
        return f"{base_name} {suffix}"

    def set_value(self, row: int, column: int, value: str) -> None:
        if row >= len(self._df):
            for _ in range(row - len(self._df) + 1):
                self.add_row()
        self._df.iat[row, column] = value
        idx = self.index(row, column)
        self.dataChanged.emit(idx, idx, [Qt.DisplayRole, Qt.EditRole])
