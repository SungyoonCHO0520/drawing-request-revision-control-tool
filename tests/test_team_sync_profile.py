from __future__ import annotations

import json

from src.team_sync.profile import load_profile, profile_for_developer, save_profile


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

