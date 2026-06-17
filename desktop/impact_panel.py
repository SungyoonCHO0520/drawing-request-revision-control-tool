from __future__ import annotations

from PySide6.QtWidgets import QTextEdit


class ImpactPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("선택한 Module의 입력 예시와 작성 요령이 표시됩니다.")

    def show_text(self, text: str) -> None:
        self.setPlainText(text)
