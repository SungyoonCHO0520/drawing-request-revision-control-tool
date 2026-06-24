from __future__ import annotations

from desktop.main_window import MainWindow, TEAM_SYNC_PASSWORD


def test_team_sync_password_accepts_developer_password():
    assert MainWindow._is_team_sync_password_valid(TEAM_SYNC_PASSWORD)


def test_team_sync_password_rejects_other_values():
    assert not MainWindow._is_team_sync_password_valid("")
    assert not MainWindow._is_team_sync_password_valid("wrong-password")
