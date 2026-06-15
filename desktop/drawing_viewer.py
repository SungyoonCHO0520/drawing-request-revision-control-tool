from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DrawingViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Drawing Viewer: 향후 도면 PDF 미리보기 영역")
        label.setWordWrap(True)
        layout.addWidget(label)
