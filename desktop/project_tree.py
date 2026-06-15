from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem

from src.data_models import MODULE_KEY_TO_TABLE, DEFAULT_MODULE_DISPLAY_NAMES


class ProjectTree(QTreeWidget):
    renameRequested = Signal(QTreeWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Project Modules")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(lambda item, column: self.renameRequested.emit(item))

    def load_projects(self, projects: list[dict[str, object]], module_names_by_project: dict[str, dict[str, str]]) -> None:
        self.clear()
        for project in projects:
            project_id = str(project["id"])
            project_item = QTreeWidgetItem([str(project.get("project_name") or "")])
            project_item.setData(0, Qt.UserRole, project_id)
            project_item.setData(0, Qt.UserRole + 3, "project")
            self.addTopLevelItem(project_item)
            display_names = module_names_by_project.get(project_id, DEFAULT_MODULE_DISPLAY_NAMES)
            for module_key, table_name in MODULE_KEY_TO_TABLE.items():
                item = QTreeWidgetItem([display_names.get(module_key, DEFAULT_MODULE_DISPLAY_NAMES[module_key])])
                item.setData(0, Qt.UserRole, project_id)
                item.setData(0, Qt.UserRole + 1, table_name)
                item.setData(0, Qt.UserRole + 2, module_key)
                item.setData(0, Qt.UserRole + 3, "module")
                project_item.addChild(item)
            project_item.setExpanded(True)

    def _show_context_menu(self, position) -> None:
        item = self.itemAt(position)
        if item is None:
            return
        item_type = item.data(0, Qt.UserRole + 3)
        if item_type not in {"project", "module"}:
            return
        menu = QMenu(self)
        action = menu.addAction("Rename Project" if item_type == "project" else "Rename Module")
        selected = menu.exec(self.viewport().mapToGlobal(position))
        if selected == action:
            self.renameRequested.emit(item)

    def select_project(self, project_id: str) -> None:
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            if item.data(0, Qt.UserRole) == str(project_id):
                self.setCurrentItem(item)
                return

    def selected_project_id(self) -> str | None:
        items = self.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def selected_table(self) -> str | None:
        items = self.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole + 1)

    def selected_module_key(self) -> str | None:
        items = self.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole + 2)

    def selected_item_type(self) -> str | None:
        items = self.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole + 3)
