from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.data_models import DEFAULT_MODULE_DISPLAY_NAMES, DEFAULT_PROJECT_NAME, MODULE_LABELS, TABLE_SCHEMAS, normalize_all, normalize_dataframe
from src.database import (
    add_project_record,
    create_project,
    delete_project_record,
    list_module_display_names,
    list_projects,
    load_cell_styles,
    load_project,
    rename_module_display,
    rename_project,
    save_cell_styles,
    save_project,
)
from src.excel_exporter import export_dataframes_to_excel
from src.excel_importer import import_excel_to_dataframes
from src.impact_rules import generate_inspection_revision_impact, generate_revision_impact, match_impact_rule
from src.inspection_pdf_parser import parse_inspection_pdf
from src.measurement_checker import check_measurement_results
from src.module_guidance import module_guidance
from src.team_sync.profile import PROJECT_ROOT, load_profile
from src.team_sync.sync_service import SyncService
from src.validators import generate_review_checklist, validate_project
from .excel_like_table import ExcelLikeTable
from .impact_panel import ImpactPanel
from .project_tree import ProjectTree
from .table_model import PandasTableModel
from .team_sync_dialog import ProfileDialog, TeamSyncDialog
from .validation_panel import ValidationPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawing Request & Revision Control Tool")
        self.resize(1500, 900)
        self.project_path: Path | None = None
        self.projects = [{"id": "1", "project_name": DEFAULT_PROJECT_NAME}]
        self.module_names_by_project = {"1": DEFAULT_MODULE_DISPLAY_NAMES.copy()}
        self.current_project_id = "1"
        self.dataframes = self._blank_project_data()
        self.project_dataframes = {"1": self.dataframes}
        self.project_cell_styles: dict[str, dict[str, dict[tuple[int, str], str]]] = {"1": {}}
        self.current_table = "drawing_request_summary"
        self._build_ui()
        self._place_window_on_screen()
        self._refresh_tree()
        self._load_table(self.current_table, sync=False)
        self._setup_team_sync_timer()

    def _blank_project_data(self) -> dict[str, pd.DataFrame]:
        return normalize_all({table: pd.DataFrame(columns=columns) for table, columns in TABLE_SCHEMAS.items()})

    def _place_window_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1500, 900)
            return
        available = screen.availableGeometry()
        width = min(1500, max(900, available.width() - 80))
        height = min(900, max(650, available.height() - 80))
        x = available.x() + (available.width() - width) // 2
        y = available.y() + (available.height() - height) // 2
        self.setGeometry(x, y, width, height)

    def _build_ui(self) -> None:
        self._build_team_sync_menu()
        self._build_toolbar()

        self.tree = ProjectTree()
        self.tree.itemSelectionChanged.connect(self._tree_changed)
        self.tree.renameRequested.connect(self.rename_tree_item)

        self.table = ExcelLikeTable()

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("선택 행 상세"))
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setPlaceholderText("선택한 행의 상세 내용이 표시됩니다.")
        self.impact_panel = ImpactPanel()
        right_layout.addWidget(self.detail, 1)
        right_layout.addWidget(QLabel("입력 예시 / 작성 요령"))
        right_layout.addWidget(self.impact_panel, 1)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        button_row = QHBoxLayout()
        add_row_above_button = QPushButton("Insert Row Above")
        add_row_above_button.clicked.connect(self.table.insert_row_above)
        add_row_below_button = QPushButton("Insert Row Below")
        add_row_below_button.clicked.connect(self.table.insert_row_below)
        add_column_left_button = QPushButton("Insert Column Left")
        add_column_left_button.clicked.connect(self.table.insert_column_left)
        add_column_right_button = QPushButton("Insert Column Right")
        add_column_right_button.clicked.connect(self.table.insert_column_right)
        delete_button = QPushButton("Delete Row")
        delete_button.clicked.connect(self.delete_current_row)
        delete_column_button = QPushButton("Delete Column")
        delete_column_button.clicked.connect(self.delete_current_column)
        cell_color_button = QPushButton("Cell Color")
        cell_color_button.clicked.connect(self.set_selected_cell_color)
        clear_color_button = QPushButton("Clear Color")
        clear_color_button.clicked.connect(self.clear_selected_cell_color)
        button_row.addWidget(add_row_above_button)
        button_row.addWidget(add_row_below_button)
        button_row.addWidget(add_column_left_button)
        button_row.addWidget(add_column_right_button)
        button_row.addWidget(delete_button)
        button_row.addWidget(delete_column_button)
        button_row.addWidget(cell_color_button)
        button_row.addWidget(clear_color_button)
        button_row.addStretch()
        center_layout.addLayout(button_row)
        center_layout.addWidget(self.table)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        project_button_row = QHBoxLayout()
        add_project_button = QPushButton("Add Project")
        add_project_button.clicked.connect(self.add_project)
        delete_project_button = QPushButton("Delete Project")
        delete_project_button.clicked.connect(self.delete_project)
        project_button_row.addWidget(add_project_button)
        project_button_row.addWidget(delete_project_button)
        left_layout.addLayout(project_button_row)
        left_layout.addWidget(self.tree)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([220, 880, 360])

        self.validation_panel = ValidationPanel()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        bottom = QSplitter(Qt.Horizontal)
        bottom.addWidget(self.validation_panel)
        bottom.addWidget(self.log)
        bottom.setSizes([700, 500])

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.addWidget(splitter, 4)
        root_layout.addWidget(bottom, 1)
        self.setCentralWidget(root)

        self.table.selectionModel()

    def _build_team_sync_menu(self) -> None:
        menu = self.menuBar().addMenu("Team Sync")
        open_action = QAction("Team Sync Manager", self)
        open_action.triggered.connect(self.open_team_sync_manager)
        menu.addAction(open_action)
        profile_action = QAction("개발자 프로필 / 자동 동기화 설정", self)
        profile_action.triggered.connect(self.change_team_profile)
        menu.addAction(profile_action)

    def _setup_team_sync_timer(self) -> None:
        self.team_sync_service = SyncService(PROJECT_ROOT)
        self.team_sync_timer = QTimer(self)
        self.team_sync_timer.setInterval(5 * 60 * 1000)
        self.team_sync_timer.timeout.connect(self._periodic_team_sync_check)
        profile = load_profile(PROJECT_ROOT)
        if profile and profile.auto_check:
            self.team_sync_timer.start()

    def open_team_sync_manager(self) -> None:
        TeamSyncDialog(PROJECT_ROOT, self).exec()
        self._restart_team_sync_timer()

    def change_team_profile(self) -> None:
        if ProfileDialog(PROJECT_ROOT, self).exec():
            self.team_sync_service = SyncService(PROJECT_ROOT)
            self._restart_team_sync_timer()
            self.statusBar().showMessage("개발자 프로필과 자동 동기화 설정을 저장했습니다.", 8000)

    def _restart_team_sync_timer(self) -> None:
        self.team_sync_timer.stop()
        profile = load_profile(PROJECT_ROOT)
        if profile and profile.auto_check:
            self.team_sync_timer.start()

    def _periodic_team_sync_check(self) -> None:
        profile = load_profile(PROJECT_ROOT)
        if not profile or not profile.auto_check:
            return
        result = self.team_sync_service.check_main_updates(apply_if_enabled=True)
        self.statusBar().showMessage(result.message, 15000)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        actions = [
            ("New Project", self.new_project),
            ("Open Project", self.open_project),
            ("Save Project", self.save_project),
            ("Import Excel", self.import_excel),
            ("Export Excel", self.export_excel),
            ("Parse Inspection PDF", self.parse_inspection_pdf),
            ("Validate", self.validate),
            ("Compare Revision", self.compare_revision),
            ("Check Measurement Data", self.check_measurement),
            ("Generate Impact Alarm", self.generate_impact_alarm),
            ("Export Report", self.export_excel),
        ]
        for label, callback in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            toolbar.addAction(action)

    def _sync_current_model(self) -> None:
        model = self.table.model()
        if model is not None:
            self.dataframes[self.current_table] = normalize_dataframe(model.dataframe(), self.current_table)
            self.project_cell_styles.setdefault(str(self.current_project_id), {})[self.current_table] = model.cell_colors()
            self.project_dataframes[str(self.current_project_id)] = self.dataframes

    def _load_table(self, table_name: str, sync: bool = True) -> None:
        if sync:
            self._sync_current_model()
        self.current_table = table_name
        table_styles = self.project_cell_styles.setdefault(str(self.current_project_id), {}).get(table_name, {})
        self.table.setModel(PandasTableModel(self.dataframes[table_name], table_styles))
        self.table.selectionModel().selectionChanged.connect(self._selection_changed)
        self.detail.clear()
        self._show_module_guidance()
        self.statusBar().showMessage(
            f"Project: {self.current_project_name()} / Loaded {MODULE_LABELS.get(table_name, table_name)}"
        )

    def _tree_changed(self) -> None:
        item_type = self.tree.selected_item_type()
        if item_type == "root":
            return
        project_id = self.tree.selected_project_id()
        if project_id and str(project_id) != str(self.current_project_id):
            self._load_project_data(str(project_id))
        table_name = self.tree.selected_table()
        if not table_name and item_type == "project":
            table_name = "drawing_request_summary"
        if table_name:
            self._load_table(table_name, sync=False)

    def _refresh_tree(self) -> None:
        self.tree.blockSignals(True)
        self.tree.load_projects(self.projects, self.module_names_by_project)
        self.tree.blockSignals(False)
        self.tree.select_project(str(self.current_project_id))

    def _load_project_data(self, project_id: str) -> None:
        self._sync_current_model()
        self.current_project_id = str(project_id)
        if project_id not in self.project_dataframes:
            if self.project_path is not None:
                self.project_dataframes[project_id] = load_project(self.project_path, project_id)
                self.project_cell_styles[project_id] = load_cell_styles(self.project_path, project_id)
            else:
                self.project_dataframes[project_id] = self._blank_project_data()
                self.project_cell_styles[project_id] = {}
        self.dataframes = self.project_dataframes[project_id]

    def current_project_name(self, project_id: str | None = None) -> str:
        project_id = str(project_id or self.current_project_id)
        for project in self.projects:
            if str(project["id"]) == project_id:
                return str(project.get("project_name") or DEFAULT_PROJECT_NAME)
        return DEFAULT_PROJECT_NAME

    def _apply_current_project_name_to_summary(
        self,
        dataframes: dict[str, pd.DataFrame] | None = None,
        project_id: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        project_id = str(project_id or self.current_project_id)
        target = dataframes or self.dataframes
        summary = normalize_dataframe(target.get("drawing_request_summary"), "drawing_request_summary")
        if summary.empty:
            summary.loc[0] = {column: "" for column in summary.columns}
        summary.loc[0, "Project"] = self.current_project_name(project_id)
        module_names = self.module_names_by_project.get(project_id, DEFAULT_MODULE_DISPLAY_NAMES)
        remark = str(summary.loc[0, "Remark"] or "")
        display_note = "Module display names: " + ", ".join(f"{key}={value}" for key, value in module_names.items())
        if "Module display names:" not in remark:
            summary.loc[0, "Remark"] = (remark + " | " + display_note).strip(" |")
        target["drawing_request_summary"] = summary
        return target

    def _selection_changed(self) -> None:
        indexes = self.table.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        df = self.table.model().dataframe()
        if row >= len(df):
            return
        record = df.iloc[row].to_dict()
        self.detail.setPlainText("\n".join(f"{key}: {value}" for key, value in record.items()))
        rule = match_impact_rule(str(record.get("Item", record.get("Part Name", ""))), str(record.get("Symbol", "")))
        self._show_module_guidance(
            f"[선택 행 Impact]\n"
            f"- Impact Area: {rule.impact_area}\n"
            f"- Required Check: {rule.required_check}\n"
            f"- Alarm Level: {rule.alarm_level}"
        )

    def _show_module_guidance(self, extra_text: str = "") -> None:
        text = module_guidance(self.current_table)
        if extra_text:
            text = f"{text}\n\n{extra_text}"
        self.impact_panel.show_text(text)

    def log_message(self, message: str) -> None:
        self.log.append(message)
        self.statusBar().showMessage(message)

    def delete_current_row(self) -> None:
        row = self.table.current_row()
        if row is None:
            QMessageBox.information(self, "Delete Row", "삭제할 행을 먼저 선택하세요.")
            return
        reply = QMessageBox.question(
            self,
            "Delete Row",
            f"선택된 {row + 1}번 행을 삭제할까요?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if self.table.delete_current_row():
            self.log_message(f"Deleted row {row + 1} from {MODULE_LABELS.get(self.current_table, self.current_table)}.")

    def delete_current_column(self) -> None:
        column_name = self.table.current_column_name()
        if column_name is None:
            QMessageBox.information(self, "Delete Column", "삭제할 열을 먼저 선택하세요.")
            return
        reply = QMessageBox.question(
            self,
            "Delete Column",
            f"선택된 '{column_name}' 열을 삭제할까요?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        deleted = self.table.delete_current_column()
        if deleted:
            self.log_message(f"Deleted column '{deleted}' from {MODULE_LABELS.get(self.current_table, self.current_table)}.")

    def new_project(self) -> None:
        self._sync_current_model()
        self.projects = [{"id": "1", "project_name": DEFAULT_PROJECT_NAME}]
        self.module_names_by_project = {"1": DEFAULT_MODULE_DISPLAY_NAMES.copy()}
        self.current_project_id = "1"
        self.dataframes = self._blank_project_data()
        self.project_dataframes = {"1": self.dataframes}
        self.project_cell_styles = {"1": {}}
        self.project_path = None
        self._refresh_tree()
        self._load_table("drawing_request_summary", sync=False)
        self.log_message("New blank project created in memory.")

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "PFC Project (*.pfcproj *.db)")
        if not path:
            return
        self.project_path = Path(path)
        self.projects = list_projects(path)
        self.current_project_id = str(self.projects[0]["id"])
        self.module_names_by_project = {
            str(project["id"]): list_module_display_names(path, project["id"])
            for project in self.projects
        }
        self.dataframes = load_project(path, self.current_project_id)
        self.project_dataframes = {self.current_project_id: self.dataframes}
        self.project_cell_styles = {self.current_project_id: load_cell_styles(path, self.current_project_id)}
        self._refresh_tree()
        self._load_table("drawing_request_summary", sync=False)
        self.log_message(f"Opened project: {path}")

    def save_project(self) -> None:
        self._sync_current_model()
        if self.project_path is None:
            path, _ = QFileDialog.getSaveFileName(self, "Save Project", "PFC_IN_Project.pfcproj", "PFC Project (*.pfcproj *.db)")
            if not path:
                return
            self.project_path = Path(path)
            create_project(self.project_path)
            self.projects = list_projects(self.project_path)
            self.current_project_id = str(self.projects[0]["id"])
            self.module_names_by_project = {
                str(project["id"]): list_module_display_names(self.project_path, project["id"])
                for project in self.projects
            }
        for project_id, dataframes in self.project_dataframes.items():
            save_project(self.project_path, self._apply_current_project_name_to_summary(dataframes, project_id), project_id)
            save_cell_styles(self.project_path, self.project_cell_styles.get(str(project_id), {}), project_id)
        self.log_message(f"Saved project: {self.project_path}")

    def add_project(self) -> None:
        if self.project_path is None:
            QMessageBox.information(self, "Add Project", "프로젝트를 추가하려면 먼저 Save Project로 .pfcproj 파일을 저장하세요.")
            return
        name, ok = QInputDialog.getText(self, "Add Project", "새 프로젝트명을 입력하세요:")
        name = name.strip()
        if not ok or not name:
            return
        project_id = add_project_record(self.project_path, name)
        self.projects = list_projects(self.project_path)
        self.module_names_by_project[str(project_id)] = list_module_display_names(self.project_path, project_id)
        self.project_dataframes[str(project_id)] = self._blank_project_data()
        self.project_cell_styles[str(project_id)] = {}
        save_project(self.project_path, self.project_dataframes[str(project_id)], project_id)
        self._load_project_data(str(project_id))
        self._refresh_tree()
        self._load_table("drawing_request_summary", sync=False)
        self.log_message(f"Added project: {name}")

    def delete_project(self) -> None:
        if self.project_path is None:
            QMessageBox.information(self, "Delete Project", "프로젝트를 삭제하려면 먼저 .pfcproj 파일을 저장하거나 열어주세요.")
            return
        project_id = self.tree.selected_project_id()
        if not project_id:
            QMessageBox.information(self, "Delete Project", "삭제할 프로젝트를 먼저 선택하세요.")
            return
        if len(self.projects) <= 1:
            QMessageBox.information(self, "Delete Project", "마지막 남은 프로젝트는 삭제할 수 없습니다.")
            return
        project_name = self.current_project_name(str(project_id))
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"'{project_name}' 프로젝트와 해당 프로젝트의 모든 Table 데이터를 삭제할까요?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._sync_current_model()
        for cached_project_id, dataframes in list(self.project_dataframes.items()):
            if str(cached_project_id) != str(project_id):
                save_project(
                    self.project_path,
                    self._apply_current_project_name_to_summary(dataframes, str(cached_project_id)),
                    cached_project_id,
                )
        delete_project_record(self.project_path, project_id)
        deleted_current_project = str(project_id) == str(self.current_project_id)
        self.project_dataframes.pop(str(project_id), None)
        self.module_names_by_project.pop(str(project_id), None)
        self.project_cell_styles.pop(str(project_id), None)
        self.projects = list_projects(self.project_path)
        self.module_names_by_project = {
            str(project["id"]): list_module_display_names(self.project_path, project["id"])
            for project in self.projects
        }
        if deleted_current_project:
            self.current_project_id = str(self.projects[0]["id"])
            self.dataframes = load_project(self.project_path, self.current_project_id)
            self.project_cell_styles[self.current_project_id] = load_cell_styles(self.project_path, self.current_project_id)
            self.project_dataframes[self.current_project_id] = self.dataframes
        else:
            self.dataframes = self.project_dataframes.get(
                str(self.current_project_id),
                load_project(self.project_path, self.current_project_id),
            )
            self.project_dataframes[str(self.current_project_id)] = self.dataframes
            self.project_cell_styles.setdefault(
                str(self.current_project_id),
                load_cell_styles(self.project_path, self.current_project_id),
            )
        self._refresh_tree()
        self._load_table("drawing_request_summary", sync=False)
        self.log_message(f"Deleted project: {project_name}")

    def set_selected_cell_color(self) -> None:
        indexes = self.table.selectedIndexes()
        if not indexes:
            QMessageBox.information(self, "Cell Color", "색상을 적용할 셀을 먼저 선택하세요.")
            return
        color = QColorDialog.getColor(parent=self, title="Select Cell Color")
        if not color.isValid():
            return
        model = self.table.model()
        if model is None:
            return
        model.set_cell_color(indexes, color.name().upper())
        self.project_cell_styles.setdefault(str(self.current_project_id), {})[self.current_table] = model.cell_colors()
        self.log_message(f"Applied cell color {color.name().upper()} to {len(indexes)} selected cell(s).")

    def clear_selected_cell_color(self) -> None:
        indexes = self.table.selectedIndexes()
        if not indexes:
            QMessageBox.information(self, "Clear Color", "색상을 지울 셀을 먼저 선택하세요.")
            return
        model = self.table.model()
        if model is None:
            return
        model.clear_cell_color(indexes)
        self.project_cell_styles.setdefault(str(self.current_project_id), {})[self.current_table] = model.cell_colors()
        self.log_message(f"Cleared cell color from {len(indexes)} selected cell(s).")

    def rename_tree_item(self, item) -> None:
        item_type = item.data(0, Qt.UserRole + 3)
        if item_type not in {"project", "module"}:
            return
        current_name = item.text(0)
        title = "Rename Project" if item_type == "project" else "Rename Module"
        new_name, ok = QInputDialog.getText(self, title, "새 이름을 입력하세요:", text=current_name)
        new_name = new_name.strip()
        if not ok or not new_name:
            return
        project_id = str(item.data(0, Qt.UserRole))
        if item_type == "project":
            for project in self.projects:
                if str(project["id"]) == project_id:
                    project["project_name"] = new_name
                    break
            if self.project_path is not None:
                rename_project(self.project_path, project_id, new_name)
        else:
            module_key = item.data(0, Qt.UserRole + 2)
            self.module_names_by_project.setdefault(project_id, DEFAULT_MODULE_DISPLAY_NAMES.copy())[module_key] = new_name
            if self.project_path is not None:
                rename_module_display(self.project_path, project_id, module_key, new_name)
        self._refresh_tree()
        self.log_message(f"{title}: {current_name} -> {new_name}")

    def import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Excel", "", "Excel (*.xlsx)")
        if not path:
            return
        dataframes, warnings = import_excel_to_dataframes(path)
        self._sync_current_model()
        self.dataframes.update(dataframes)
        self._load_table("drawing_request_summary")
        self.log_message(f"Imported Excel: {path}")
        for warning in warnings:
            self.log_message(f"WARNING: {warning}")

    def export_excel(self) -> None:
        self._sync_current_model()
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "PFC_IN_Request_Package.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        export_dataframes_to_excel(self._apply_current_project_name_to_summary(self.dataframes), path)
        self.log_message(f"Exported Excel: {path}")

    def parse_inspection_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Parse Inspection PDF", "", "PDF (*.pdf)")
        if not path:
            return
        raw_df, draft_df = parse_inspection_pdf(path)
        self._sync_current_model()
        self.dataframes["raw_ocr_text"] = pd.concat([self.dataframes["raw_ocr_text"], raw_df], ignore_index=True)
        self.dataframes["inspection_standard_db"] = pd.concat([self.dataframes["inspection_standard_db"], draft_df], ignore_index=True)
        self._load_table("inspection_standard_db")
        self.log_message(f"Inspection PDF parsed. raw={len(raw_df)}, candidates={len(draft_df)}")

    def validate(self) -> None:
        self._sync_current_model()
        self.dataframes["drawing_review_checklist"] = generate_review_checklist(self.dataframes)
        result = validate_project(self.dataframes)
        self.validation_panel.show_summary(result)
        self.log_message(f"Validation completed. issues={len(result)}")

    def compare_revision(self) -> None:
        QMessageBox.information(self, "Compare Revision", "CLI compare 또는 두 프로젝트 선택 비교 기능은 다음 단계에서 UI를 확장합니다.")

    def check_measurement(self) -> None:
        self._sync_current_model()
        self.dataframes["measurement_result_db"] = check_measurement_results(
            self.dataframes["measurement_result_db"], self.dataframes["inspection_standard_db"]
        )
        self._load_table("measurement_result_db")
        self.log_message("Measurement data checked.")

    def generate_impact_alarm(self) -> None:
        self._sync_current_model()
        self.dataframes["revision_impact"] = generate_revision_impact(self.dataframes["change_history"])
        self.dataframes["inspection_revision_impact"] = generate_inspection_revision_impact(
            self.dataframes["revision_impact"],
            self.dataframes["inspection_standard_db"],
            self.dataframes["measurement_result_db"],
        )
        self._load_table("revision_impact")
        self.log_message("Impact alarms generated.")
