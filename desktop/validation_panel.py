from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import QTextEdit


class ValidationPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Validate 결과, PASS/NG/CHECK/MISSING 요약이 표시됩니다.")

    def show_summary(self, validation_df: pd.DataFrame) -> None:
        if validation_df.empty:
            self.setPlainText("Validation PASS: 누락/오류 알람이 없습니다.")
            return
        summary = validation_df.groupby(["Result", "Alarm Level"]).size().reset_index(name="Count")
        self.setPlainText(summary.to_string(index=False) + "\n\n" + validation_df.head(50).to_string(index=False))
