from __future__ import annotations

from PySide6.QtWidgets import QTextEdit


class ImpactPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("선택 행의 Impact Rule과 Revision 영향 알람이 표시됩니다.")

    def show_text(self, text: str) -> None:
        self.setPlainText(text)
