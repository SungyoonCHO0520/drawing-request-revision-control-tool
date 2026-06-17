from __future__ import annotations

from src.module_guidance import module_guidance


def test_module_guidance_returns_summary_example():
    text = module_guidance("drawing_request_summary")

    assert "Summary 입력 예시" in text
    assert "Project" in text


def test_module_guidance_returns_fallback_for_unknown_table():
    text = module_guidance("unknown")

    assert "선택한 Module" in text
