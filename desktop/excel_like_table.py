from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QComboBox, QInputDialog, QMenu, QMessageBox, QStyledItemDelegate, QTableView

from src.data_models import DROPDOWN_COLUMNS


class ComboDelegate(QStyledItemDelegate):
    def __init__(self, options: list[str], parent=None):
        super().__init__(parent)
        self.options = options

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems([""] + self.options)
        return combo

    def setEditorData(self, editor, index):
        value = str(index.model().data(index, Qt.EditRole) or "")
        position = editor.findText(value)
        editor.setCurrentIndex(max(position, 0))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)


class ExcelLikeTable(QTableView):
    columnHeaderRenamed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectItems)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().sectionDoubleClicked.connect(self.rename_column_header)
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self._show_header_context_menu)
        self.verticalHeader().setVisible(True)
        self._apply_grid_style()
        self._install_actions()

    def _apply_grid_style(self) -> None:
        """입력 칸을 또렷한 선으로 구분되게 표시한다."""
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        # gridline-color/헤더 테두리만 지정한다. 셀 background-color를 지정하면
        # 모델의 BackgroundRole(셀 색상 기능)과 교차 행 색상이 덮어써지므로 건드리지 않는다.
        self.setStyleSheet(
            """
            QTableView {
                gridline-color: #9aa0a6;
                border: 1px solid #9aa0a6;
            }
            QHeaderView::section {
                background-color: #f2f3f5;
                color: #1f2933;
                border: none;
                border-right: 1px solid #9aa0a6;
                border-bottom: 1px solid #9aa0a6;
                padding: 4px;
            }
            QTableCornerButton::section {
                background-color: #f2f3f5;
                border: none;
                border-right: 1px solid #9aa0a6;
                border-bottom: 1px solid #9aa0a6;
            }
            """
        )

    def _install_actions(self) -> None:
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_selection)
        self.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_selection)
        self.addAction(paste_action)

    def setModel(self, model) -> None:
        super().setModel(model)
        self.apply_delegates()
        self.resizeColumnsToContents()

    def apply_delegates(self) -> None:
        model = self.model()
        if model is None:
            return
        for col in range(model.columnCount()):
            self.setItemDelegateForColumn(col, QStyledItemDelegate(self))
            if hasattr(model, "internal_column_name"):
                column_name = model.internal_column_name(col)
            else:
                column_name = str(model.headerData(col, Qt.Horizontal, Qt.DisplayRole))
            if column_name in DROPDOWN_COLUMNS:
                self.setItemDelegateForColumn(col, ComboDelegate(DROPDOWN_COLUMNS[column_name], self))

    def _show_header_context_menu(self, position) -> None:
        section = self.horizontalHeader().logicalIndexAt(position)
        if section < 0:
            return
        menu = QMenu(self)
        rename_action = menu.addAction("Rename Column")
        selected = menu.exec(self.horizontalHeader().mapToGlobal(position))
        if selected == rename_action:
            self.rename_column_header(section)

    def rename_column_header(self, section: int, new_name: str | None = None) -> bool:
        model = self.model()
        if model is None or not hasattr(model, "rename_header"):
            return False
        old_name = str(model.headerData(section, Qt.Horizontal, Qt.DisplayRole))
        if new_name is None:
            new_name, accepted = QInputDialog.getText(
                self,
                "Rename Column",
                "새 열 제목을 입력하세요.",
                text=old_name,
            )
            if not accepted:
                return False
        try:
            previous, renamed = model.rename_header(section, new_name)
        except ValueError as error:
            QMessageBox.warning(self, "Rename Column", str(error))
            return False
        self.apply_delegates()
        self.resizeColumnToContents(section)
        self.columnHeaderRenamed.emit(previous, renamed)
        return True

    def copy_selection(self) -> None:
        indexes = self.selectedIndexes()
        if not indexes:
            return
        rows = sorted(set(index.row() for index in indexes))
        cols = sorted(set(index.column() for index in indexes))
        model = self.model()
        text_rows = []
        for row in rows:
            text_rows.append("\t".join(str(model.data(model.index(row, col), Qt.DisplayRole) or "") for col in cols))
        QApplication.clipboard().setText("\n".join(text_rows))

    def paste_selection(self) -> None:
        model = self.model()
        if model is None:
            return
        start = self.currentIndex()
        if not start.isValid():
            return
        text = QApplication.clipboard().text()
        for row_offset, line in enumerate(text.splitlines()):
            for col_offset, value in enumerate(line.split("\t")):
                row = start.row() + row_offset
                col = start.column() + col_offset
                if col < model.columnCount():
                    model.set_value(row, col, value)

    def selected_cell(self) -> tuple[int, int] | None:
        current = self.currentIndex()
        if current.isValid():
            return current.row(), current.column()
        indexes = self.selectedIndexes()
        if indexes:
            first = indexes[0]
            return first.row(), first.column()
        return None

    def add_row(self) -> None:
        if self.model():
            self.model().add_row()

    def insert_row_above(self) -> None:
        if not self.model():
            return
        selected = self.selected_cell()
        self.model().insert_row(0 if selected is None else selected[0])

    def insert_row_below(self) -> None:
        if not self.model():
            return
        selected = self.selected_cell()
        self.model().insert_row(self.model().rowCount() if selected is None else selected[0] + 1)

    def insert_column_left(self) -> None:
        if not self.model():
            return
        selected = self.selected_cell()
        self.model().insert_column(0 if selected is None else selected[1])
        self.apply_delegates()

    def insert_column_right(self) -> None:
        if not self.model():
            return
        selected = self.selected_cell()
        self.model().insert_column(self.model().columnCount() if selected is None else selected[1] + 1)
        self.apply_delegates()

    def current_row(self) -> int | None:
        selected = self.selected_cell()
        if selected is None:
            return None
        return selected[0]

    def current_column(self) -> int | None:
        selected = self.selected_cell()
        if selected is None:
            return None
        return selected[1]

    def delete_current_row(self) -> bool:
        row = self.current_row()
        if row is None or not self.model():
            return False
        self.model().delete_row(row)
        return True

    def current_column_name(self) -> str | None:
        column = self.current_column()
        if column is None or not self.model():
            return None
        return str(self.model().headerData(column, Qt.Horizontal, Qt.DisplayRole))

    def delete_current_column(self) -> str | None:
        column = self.current_column()
        if column is None or not self.model():
            return None
        deleted = self.model().delete_column(column)
        self.apply_delegates()
        return deleted
