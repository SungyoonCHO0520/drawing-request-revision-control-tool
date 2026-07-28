from __future__ import annotations

import json
from pathlib import Path

from src.team_sync.profile import (
    fallback_profile_path,
    load_profile,
    profile_for_developer,
    profile_path,
    save_profile,
    temporary_profile_path,
)


def test_team_profile_save_and_load(tmp_path):
    profile = profile_for_developer("성윤")
    profile.auto_merge = True
    save_profile(profile, tmp_path)

    loaded = load_profile(tmp_path)

    assert loaded is not None
    assert loaded.developer_name == "성윤"
    assert loaded.branch_name == "sungyoon-codex"
    assert loaded.development_tool == "Codex"
    assert loaded.auto_merge is True
    payload = json.loads((tmp_path / ".team_profile.local.json").read_text(encoding="utf-8"))
    assert payload["branch_name"] == "sungyoon-codex"


def test_second_developer_profile_uses_claude_branch(tmp_path):
    profile = profile_for_developer("학석")
    save_profile(profile, tmp_path)

    loaded = load_profile(tmp_path)

    assert loaded is not None
    assert loaded.branch_name == "hakseok-claude"
    assert loaded.development_tool == "Claude Code"


def test_profile_falls_back_to_local_app_data_when_project_is_not_writable(
    tmp_path,
    monkeypatch,
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    local_app_data = tmp_path / "local-app-data"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    primary = profile_path(project_root)
    original_write_text = Path.write_text

    def write_text_with_blocked_project(self, data, *args, **kwargs):
        if self == primary:
            raise PermissionError(13, "Permission denied", str(self))
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", write_text_with_blocked_project)
    profile = profile_for_developer("성윤")
    profile.last_main_commit = "main123"

    saved_path = save_profile(profile, project_root)
    loaded = load_profile(project_root)

    assert saved_path == fallback_profile_path(project_root)
    assert saved_path.is_file()
    assert loaded is not None
    assert loaded.last_main_commit == "main123"


def test_profile_uses_temp_when_project_and_local_app_data_are_blocked(
    tmp_path,
    monkeypatch,
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local-app-data"))
    monkeypatch.setattr("src.team_sync.profile.tempfile.tempdir", str(tmp_path / "temp"))
    blocked_paths = {
        profile_path(project_root),
        fallback_profile_path(project_root),
    }
    original_write_text = Path.write_text

    def write_text_with_blocked_locations(self, data, *args, **kwargs):
        if self in blocked_paths:
            raise PermissionError(13, "Permission denied", str(self))
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", write_text_with_blocked_locations)
    profile = profile_for_developer("성윤")
    profile.last_main_commit = "temp-main"

    saved_path = save_profile(profile, project_root)
    loaded = load_profile(project_root)

    assert saved_path == temporary_profile_path(project_root)
    assert loaded is not None
    assert loaded.last_main_commit == "temp-main"

