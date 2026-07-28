from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILENAME = ".team_profile.local.json"

DEVELOPER_PROFILES = {
    "성윤": {"branch_name": "sungyoon-codex", "development_tool": "Codex"},
    "학석": {"branch_name": "hakseok-claude", "development_tool": "Claude Code"},
}


@dataclass
class TeamProfile:
    developer_name: str
    branch_name: str
    development_tool: str
    auto_check: bool = True
    auto_merge: bool = False
    last_main_commit: str = ""
    last_sync_at: str = ""


def profile_path(project_root: str | Path | None = None) -> Path:
    return Path(project_root or PROJECT_ROOT) / PROFILE_FILENAME


def fallback_profile_path(project_root: str | Path | None = None) -> Path:
    root = Path(project_root or PROJECT_ROOT).resolve()
    root_key = hashlib.sha256(str(root).casefold().encode("utf-8")).hexdigest()[:16]
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "DrawingRequestRevisionTool" / "profiles" / f"{root_key}.json"


def temporary_profile_path(project_root: str | Path | None = None) -> Path:
    root = Path(project_root or PROJECT_ROOT).resolve()
    root_key = hashlib.sha256(str(root).casefold().encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / "DrawingRequestRevisionTool" / "profiles" / f"{root_key}.json"


def profile_for_developer(name: str) -> TeamProfile:
    try:
        values = DEVELOPER_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown developer profile: {name}") from exc
    return TeamProfile(name, values["branch_name"], values["development_tool"])


def save_profile(profile: TeamProfile, project_root: str | Path | None = None) -> Path:
    contents = json.dumps(asdict(profile), ensure_ascii=False, indent=2)
    paths = [
        profile_path(project_root),
        fallback_profile_path(project_root),
        temporary_profile_path(project_root),
    ]
    last_error: OSError | None = None
    for path in paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
            return path
        except OSError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise OSError("Team Sync 프로필 저장 위치를 찾지 못했습니다.")


def load_profile(project_root: str | Path | None = None) -> TeamProfile | None:
    paths = [
        profile_path(project_root),
        fallback_profile_path(project_root),
        temporary_profile_path(project_root),
    ]
    existing_paths: list[tuple[float, Path]] = []
    for path in paths:
        try:
            if path.exists():
                existing_paths.append((path.stat().st_mtime, path))
        except OSError:
            continue
    for _, path in sorted(existing_paths, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return TeamProfile(
                developer_name=str(payload["developer_name"]),
                branch_name=str(payload["branch_name"]),
                development_tool=str(payload["development_tool"]),
                auto_check=bool(payload.get("auto_check", True)),
                auto_merge=bool(payload.get("auto_merge", False)),
                last_main_commit=str(payload.get("last_main_commit", "")),
                last_sync_at=str(payload.get("last_sync_at", "")),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return None

