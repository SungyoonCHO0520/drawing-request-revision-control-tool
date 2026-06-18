from src.team_sync.security_check import find_sensitive_paths, is_sensitive_path


def test_sensitive_company_files_are_blocked():
    paths = [
        "src/app.py",
        "drawings/customer.pdf",
        "reports/result.xlsx",
        "sample.pfcproj",
        ".venv/Lib/site.py",
        ".env.production",
    ]

    found = find_sensitive_paths(paths)

    assert "src/app.py" not in found
    assert "drawings/customer.pdf" in found
    assert "reports/result.xlsx" in found
    assert "sample.pfcproj" in found
    assert ".venv/Lib/site.py" in found
    assert ".env.production" in found
    assert is_sensitive_path("desktop/main_window.py") is False

