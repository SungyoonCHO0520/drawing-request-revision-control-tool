from __future__ import annotations

import time

from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.team_sync_dialog import TeamSyncDialog
from src.team_sync.result_models import SyncResult


class DialogServiceStub:
    def status(self, fetch=False):
        from src.team_sync.result_models import SyncStatus

        return SyncStatus(sync_state="Up to date")

    def check_main_updates(self):
        return SyncResult(True, "최신 Main 확인 완료", commit_id="main123")


def test_check_main_shows_progress_and_finishes_in_background(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    dialog = TeamSyncDialog(tmp_path)
    dialog.service = DialogServiceStub()

    dialog.check_main()

    assert dialog.progress_bar.isHidden() is False
    assert "진행 중" in dialog.output.toPlainText()

    deadline = time.monotonic() + 3
    while dialog.sync_thread is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)

    assert dialog.sync_thread is None
    assert dialog.progress_bar.isHidden() is True
    assert "최신 Main 확인 완료" in dialog.output.toPlainText()
    assert "main123" in dialog.output.toPlainText()
    dialog.close()
