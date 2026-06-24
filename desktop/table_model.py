from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Signal, Qt
from PySide6.QtGui import QColor


class PandasTableModel(QAbstractTableModel):
    cellEdited = Signal(int, str, str, str)

    def __init__(
        self,
        dataframe: pd.DataFrame,
        cell_colors: dict[tuple[int, str], str] | None = None,
        header_names: dict[str, str] | None = None,
        cell_text_colors: dict[tuple[int, str], str] | None = None,
    ):
        super().__init__()
        self._df = dataframe.copy().fillna("")
        self._cell_colors = dict(cell_colors or {})
        self._cell_text_colors = dict(cell_text_colors or {})
        self._header_names = {
            str(column): str(display_name)
            for column, display_name in (header_names or {}).items()
            if column in self._df.columns and str(display_name).strip()
        }

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
        if role == Qt.ForegroundRole:
            column_name = str(self._df.columns[index.column()])
            color = self._cell_text_colors.get((index.row(), column_name))
            if color:
                return QColor(color)
        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        previous = str(self._df.iat[index.row(), index.column()])
        updated = "" if value is None else str(value)
        if previous == updated:
            return True
        self._df.iat[index.row(), index.column()] = updated
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        self.cellEdited.emit(index.row(), self.internal_column_name(index.column()), previous, updated)
        return True

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            internal_name = str(self._df.columns[section])
            if role == Qt.DisplayRole:
                return self._header_names.get(internal_name, internal_name)
            if role == Qt.UserRole:
                return internal_name
            if role == Qt.ToolTipRole:
                return "더블클릭하거나 우클릭하여 열 제목을 변경할 수 있습니다."
            return None
        if role == Qt.DisplayRole:
            return str(section + 1)
        return None

    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    def cell_colors(self) -> dict[tuple[int, str], str]:
        return dict(self._cell_colors)

    def cell_text_colors(self) -> dict[tuple[int, str], str]:
        return dict(self._cell_text_colors)

    def internal_column_name(self, column: int) -> str:
        return str(self._df.columns[column])

    def header_display_names(self) -> dict[str, str]:
        return {
            column: display_name
            for column, display_name in self._header_names.items()
            if column in self._df.columns and display_name != column
        }

    def rename_header(self, column: int, display_name: str) -> tuple[str, str]:
        if column < 0 or column >= len(self._df.columns):
            raise ValueError("변경할 열을 찾을 수 없습니다.")
        display_name = str(display_name).strip()
        if not display_name:
            raise ValueError("열 제목은 비워둘 수 없습니다.")
        internal_name = self.internal_column_name(column)
        old_display_name = str(self.headerData(column, Qt.Horizontal, Qt.DisplayRole))
        other_names = {
            str(self.headerData(index, Qt.Horizontal, Qt.DisplayRole))
            for index in range(self.columnCount())
            if index != column
        }
        if display_name in other_names:
            raise ValueError("같은 열 제목이 이미 있습니다.")
        if display_name == internal_name:
            self._header_names.pop(internal_name, None)
        else:
            self._header_names[internal_name] = display_name
        self.headerDataChanged.emit(Qt.Horizontal, column, column)
        return old_display_name, display_name

    def set_cell_color(self, indexes: list[QModelIndex], color: str) -> None:
        valid_indexes = [index for index in indexes if index.isValid()]
        if not valid_indexes:
            return
        for index in valid_indexes:
            column_name = str(self._df.columns[index.column()])
            self._cell_colors[(index.row(), column_name)] = color
        self._emit_data_changed(valid_indexes, [Qt.BackgroundRole])

    def clear_cell_color(self, indexes: list[QModelIndex]) -> None:
        valid_indexes = [index for index in indexes if index.isValid()]
        if not valid_indexes:
            return
        for index in valid_indexes:
            column_name = str(self._df.columns[index.column()])
            self._cell_colors.pop((index.row(), column_name), None)
        self._emit_data_changed(valid_indexes, [Qt.BackgroundRole])

    def set_cell_text_color(self, indexes: list[QModelIndex], color: str) -> None:
        valid_indexes = [index for index in indexes if index.isValid()]
        if not valid_indexes:
            return
        for index in valid_indexes:
            column_name = str(self._df.columns[index.column()])
            self._cell_text_colors[(index.row(), column_name)] = color
        self._emit_data_changed(valid_indexes, [Qt.ForegroundRole])

    def clear_cell_text_color(self, indexes: list[QModelIndex]) -> None:
        valid_indexes = [index for index in indexes if index.isValid()]
        if not valid_indexes:
            return
        for index in valid_indexes:
            column_name = str(self._df.columns[index.column()])
            self._cell_text_colors.pop((index.row(), column_name), None)
        self._emit_data_changed(valid_indexes, [Qt.ForegroundRole])

    def _emit_data_changed(self, indexes: list[QModelIndex], roles: list[int]) -> None:
        rows = [index.row() for index in indexes]
        columns = [index.column() for index in indexes]
        top_left = self.index(min(rows), min(columns))
        bottom_right = self.index(max(rows), max(columns))
        self.dataChanged.emit(top_left, bottom_right, roles)

    def _shift_colors_for_insert_row(self, position: int) -> None:
        shifted = {}
        for (row, column_name), color in self._cell_colors.items():
            shifted[(row + 1 if row >= position else row, column_name)] = color
        self._cell_colors = shifted
        shifted_text = {}
        for (row, column_name), color in self._cell_text_colors.items():
            shifted_text[(row + 1 if row >= position else row, column_name)] = color
        self._cell_text_colors = shifted_text

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
        shifted_text = {}
        for (row, column_name), color in self._cell_text_colors.items():
            if row in removed:
                continue
            shift = sum(1 for removed_row in removed if removed_row < row)
            shifted_text[(row - shift, column_name)] = color
        self._cell_text_colors = shifted_text

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
        self._cell_text_colors = {
            (row, name): color
            for (row, name), color in self._cell_text_colors.items()
            if name != column_name
        }
        self._header_names.pop(column_name, None)
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
        previous = str(self._df.iat[row, column])
        updated = "" if value is None else str(value)
        if previous == updated:
            return
        self._df.iat[row, column] = updated
        idx = self.index(row, column)
        self.dataChanged.emit(idx, idx, [Qt.DisplayRole, Qt.EditRole])
        self.cellEdited.emit(row, self.internal_column_name(column), previous, updated)
