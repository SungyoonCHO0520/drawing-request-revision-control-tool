from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class InspectionViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Inspection Viewer: 검사 기준서 PDF Parse 결과 확인 영역")
        label.setWordWrap(True)
        layout.addWidget(label)
