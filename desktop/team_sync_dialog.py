from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.team_sync.profile import (
    DEVELOPER_PROFILES,
    PROJECT_ROOT,
    load_profile,
    profile_for_developer,
    save_profile,
)
from src.team_sync.result_models import SyncResult
from src.team_sync.sync_service import SyncService


class ProfileDialog(QDialog):
    def __init__(self, project_root: str | Path = PROJECT_ROOT, parent=None):
        super().__init__(parent)
        self.project_root = Path(project_root)
        self.setWindowTitle("개발자 프로필 설정")
        self.setMinimumWidth(430)

        current = load_profile(self.project_root)
        self.developer_combo = QComboBox()
        for name, values in DEVELOPER_PROFILES.items():
            self.developer_combo.addItem(
                f"{name} / {values['branch_name']} / {values['development_tool']}",
                name,
            )
        if current:
            index = self.developer_combo.findData(current.developer_name)
            if index >= 0:
                self.developer_combo.setCurrentIndex(index)

        self.auto_check = QCheckBox("5분마다 새로운 Main 업데이트 확인")
        self.auto_check.setChecked(current.auto_check if current else True)
        self.auto_merge = QCheckBox("로컬 수정사항이 없을 때 Main 자동 반영")
        self.auto_merge.setChecked(current.auto_merge if current else False)

        form = QFormLayout()
        form.addRow("개발자", self.developer_combo)
        form.addRow("자동 확인", self.auto_check)
        form.addRow("자동 반영", self.auto_merge)

        note = QLabel("프로필은 이 PC에만 저장되며 GitHub에는 업로드되지 않습니다.")
        note.setWordWrap(True)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)

    def _save(self) -> None:
        profile = profile_for_developer(str(self.developer_combo.currentData()))
        profile.auto_check = self.auto_check.isChecked()
        profile.auto_merge = self.auto_merge.isChecked()
        previous = load_profile(self.project_root)
        if previous and previous.developer_name == profile.developer_name:
            profile.last_main_commit = previous.last_main_commit
            profile.last_sync_at = previous.last_sync_at
        save_profile(profile, self.project_root)
        self.accept()


def ensure_profile_selected(project_root: str | Path = PROJECT_ROOT, parent=None) -> bool:
    if load_profile(project_root) is not None:
        return True
    return ProfileDialog(project_root, parent).exec() == QDialog.Accepted


class TeamSyncDialog(QDialog):
    def __init__(self, project_root: str | Path = PROJECT_ROOT, parent=None):
        super().__init__(parent)
        self.project_root = Path(project_root)
        self.service = SyncService(self.project_root)
        self.setWindowTitle("Team Sync Manager")
        self.resize(760, 620)

        self.value_labels = {name: QLabel("-") for name in (
            "developer",
            "local_branch",
            "remote_branch",
            "local_commit",
            "main_commit",
            "local_changes",
            "sync_state",
            "last_sync",
        )}
        for key in ("local_commit", "main_commit"):
            self.value_labels[key].setTextInteractionFlags(self.value_labels[key].textInteractionFlags())

        info_group = QGroupBox("동기화 상태")
        info_form = QFormLayout(info_group)
        info_form.addRow("개발자 이름", self.value_labels["developer"])
        info_form.addRow("현재 로컬 브랜치", self.value_labels["local_branch"])
        info_form.addRow("개인 원격 브랜치", self.value_labels["remote_branch"])
        info_form.addRow("로컬 최신 Commit", self.value_labels["local_commit"])
        info_form.addRow("GitHub main 최신 Commit", self.value_labels["main_commit"])
        info_form.addRow("로컬 수정파일", self.value_labels["local_changes"])
        info_form.addRow("동기화 상태", self.value_labels["sync_state"])
        info_form.addRow("마지막 동기화", self.value_labels["last_sync"])

        button_grid = QGridLayout()
        actions = [
            ("최신 Main 확인", self.check_main),
            ("Main 변경사항 반영", self.apply_main),
            ("내 작업 업로드", self.upload_work),
            ("내 작업 Main 통합", self.integrate_work),
            ("통합 상태 확인", self.refresh_remote_status),
            ("GitHub 저장소 열기", self.open_repository),
        ]
        for index, (label, callback) in enumerate(actions):
            button = QPushButton(label)
            button.clicked.connect(callback)
            button_grid.addWidget(button, index // 2, index % 2)

        settings_button = QPushButton("개발자 프로필 및 자동 동기화 설정")
        settings_button.clicked.connect(self.change_profile)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("동기화 작업 결과와 확인할 내용이 표시됩니다.")

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        close_row.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(info_group)
        layout.addLayout(button_grid)
        layout.addWidget(settings_button)
        layout.addWidget(QLabel("작업 결과"))
        layout.addWidget(self.output, 1)
        layout.addLayout(close_row)
        self.refresh_status()

    def _show_result(self, result: SyncResult) -> None:
        lines = [result.message]
        if result.branch:
            lines.append(f"Branch: {result.branch}")
        if result.commit_id:
            lines.append(f"Commit: {result.commit_id}")
        if result.pull_request_url:
            lines.append(f"Pull Request: {result.pull_request_url}")
        if result.conflicts:
            lines.append("충돌 파일:\n- " + "\n- ".join(result.conflicts))
        if result.details:
            lines.append("상세:\n" + "\n".join(value for value in result.details if value))
        self.output.setPlainText("\n\n".join(lines))
        self.refresh_status()
        if result.success:
            QMessageBox.information(self, "Team Sync", result.message)
        else:
            QMessageBox.warning(self, "Team Sync", result.message)

    def refresh_status(self, fetch: bool = False) -> None:
        status = self.service.status(fetch=fetch)
        self.value_labels["developer"].setText(status.developer_name or "미설정")
        self.value_labels["local_branch"].setText(status.local_branch or "-")
        self.value_labels["remote_branch"].setText(status.remote_branch or "-")
        self.value_labels["local_commit"].setText(status.local_commit[:12] or "-")
        self.value_labels["main_commit"].setText(status.main_commit[:12] or "-")
        self.value_labels["local_changes"].setText("있음" if status.has_local_changes else "없음")
        self.value_labels["sync_state"].setText(status.sync_state)
        self.value_labels["last_sync"].setText(status.last_sync_at or "기록 없음")

    def check_main(self) -> None:
        self._show_result(self.service.check_main_updates())

    def apply_main(self) -> None:
        self._show_result(self.service.apply_main_changes())

    def upload_work(self) -> None:
        message, ok = QInputDialog.getText(self, "내 작업 업로드", "Commit 메시지를 입력하세요.")
        if ok and message.strip():
            self._show_result(self.service.upload_my_work(message.strip()))

    def integrate_work(self) -> None:
        answer = QMessageBox.question(
            self,
            "내 작업 Main 통합",
            "로컬 수정사항이 있으면 별도 업로드 없이 자동 Commit합니다.\n"
            "그다음 최신 Main을 반영하고 전체 테스트와 GitHub 검사를 통과하면 main에 병합합니다. 계속할까요?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self._show_result(self.service.integrate_my_work())

    def refresh_remote_status(self) -> None:
        result = self.service.check_main_updates()
        self._show_result(result)

    def open_repository(self) -> None:
        url = self.service.github.repository_url() or self.service.git.remote_url()
        if url.startswith("git@github.com:"):
            url = "https://github.com/" + url.split(":", 1)[1]
        if url.endswith(".git"):
            url = url[:-4]
        if url:
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.warning(self, "GitHub 저장소", "GitHub 저장소 주소를 찾지 못했습니다.")

    def change_profile(self) -> None:
        if ProfileDialog(self.project_root, self).exec() == QDialog.Accepted:
            self.service = SyncService(self.project_root)
            self.refresh_status()
