from __future__ import annotations

import pandas as pd

from src.impact_rules import generate_revision_impact, match_impact_rule


def test_impact_rule_matching():
    rule = match_impact_rule("Turn 변경", "N_Turn")

    assert rule.alarm_level == "High"
    assert "DCR" in rule.impact_area


def test_revision_impact_generation():
    history = pd.DataFrame(
        [
            {
                "Date": "2026-05-19",
                "User": "dev",
                "Rev": "B",
                "Changed Sheet": "electrical_spec",
                "Changed Item": "Wire 변경",
                "Changed Symbol": "Wire",
                "Before": "old",
                "After": "new",
                "Reason": "test",
                "Impact Summary": "",
                "Comment": "",
            }
        ]
    )
    impact = generate_revision_impact(history)

    assert impact.loc[0, "Alarm Level"] == "High"
    assert "DCR" in impact.loc[0, "Impact Area"]
