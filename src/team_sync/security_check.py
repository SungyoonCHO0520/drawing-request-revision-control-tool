from __future__ import annotations

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
    return path.strip().strip('"').replace("\\", "/")


def is_sensitive_path(path: str) -> bool:
    normalized = normalize_git_path(path)
    pure = PurePosixPath(normalized.lower())
    name = pure.name
    if pure.suffix in SENSITIVE_EXTENSIONS:
        return True
    if name == ".env" or name.startswith(".env."):
        return True
    return any(part in SENSITIVE_PARTS for part in pure.parts)


def find_sensitive_paths(paths: list[str]) -> list[str]:
    return sorted({normalize_git_path(path) for path in paths if is_sensitive_path(path)})

