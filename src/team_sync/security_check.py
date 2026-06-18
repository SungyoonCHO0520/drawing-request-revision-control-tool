from __future__ import annotations

import re
from pathlib import PurePosixPath


SENSITIVE_EXTENSIONS = {
    ".pdf",
    ".xls",
    ".xlsx",
    ".xlsm",
    ".csv",
    ".pfcproj",
    ".db",
    ".sqlite",
    ".sqlite3",
}
SENSITIVE_PARTS = {".venv", "venv", "secrets", "credentials", "company_data", "confidential"}


def normalize_git_path(path: str) -> str:
    return path


def is_sensitive_path(path: str) -> bool:
    parts = [part for part in re.split(r"[\\/]", path.casefold()) if part]
    if not parts:
        return False
    name = parts[-1]
    if PurePosixPath(name).suffix in SENSITIVE_EXTENSIONS:
        return True
    if name == ".env" or name.startswith(".env."):
        return True
    return any(part in SENSITIVE_PARTS for part in parts)


def find_sensitive_paths(paths: list[str]) -> list[str]:
    return sorted({path for path in paths if is_sensitive_path(path)})
