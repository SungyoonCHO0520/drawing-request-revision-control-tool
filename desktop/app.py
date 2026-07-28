from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.main_window import MainWindow
from desktop.team_sync_dialog import ensure_profile_selected
from src.team_sync.sync_service import SyncService


def _verify_packaged_dependencies() -> None:
    import fitz

    from src.inspection_pdf_parser import parse_dimension_spec

    if not fitz.VersionBind:
        raise RuntimeError("PyMuPDF is not available.")
    parsed = parse_dimension_spec("105.1±0.6")
    if parsed["upper"] != 105.7 or parsed["lower"] != 104.5:
        raise RuntimeError("Inspection dimension parser self-check failed.")


def main() -> None:
    app = QApplication(sys.argv)
    standalone = os.environ.get("PFC_STANDALONE") == "1" or not (ROOT / ".git").exists()
    if standalone:
        os.environ["PFC_STANDALONE"] = "1"
    if not standalone:
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
    if "--smoke-test" in sys.argv:
        _verify_packaged_dependencies()
        QTimer.singleShot(1000, app.quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
