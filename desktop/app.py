from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.main_window import MainWindow
from desktop.team_sync_dialog import ensure_profile_selected
from src.team_sync.sync_service import SyncService


def main() -> None:
    app = QApplication(sys.argv)
    if not ensure_profile_selected():
        return
    if os.environ.get("PFC_TEAM_SYNC_DONE") != "1":
        sync_result = SyncService(ROOT).ensure_startup_sync()
        if not sync_result.success:
            details = "\n".join(sync_result.conflicts or sync_result.details)
            QMessageBox.warning(
                None,
                "Team Sync",
                sync_result.message + (f"\n\n{details}" if details else ""),
            )
            return
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
