from __future__ import annotations

import json
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


def profile_for_developer(name: str) -> TeamProfile:
    try:
        values = DEVELOPER_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown developer profile: {name}") from exc
    return TeamProfile(name, values["branch_name"], values["development_tool"])


def save_profile(profile: TeamProfile, project_root: str | Path | None = None) -> Path:
    path = profile_path(project_root)
    path.write_text(json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_profile(project_root: str | Path | None = None) -> TeamProfile | None:
    path = profile_path(project_root)
    if not path.exists():
        return None
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
        return None

