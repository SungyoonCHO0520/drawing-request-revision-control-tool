from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.team_sync.git_service import GitService
from src.team_sync.security_check import find_sensitive_paths


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        shell=False,
        check=True,
    )


def initialized_repo(tmp_path: Path) -> GitService:
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.name", "Team Sync Test")
    run_git(tmp_path, "config", "user.email", "team-sync@example.com")
    baseline = tmp_path / "baseline.txt"
    baseline.write_text("baseline", encoding="utf-8")
    run_git(tmp_path, "add", "baseline.txt")
    run_git(tmp_path, "commit", "-m", "baseline")
    return GitService(tmp_path)


@pytest.mark.parametrize(
    "relative_path",
    [
        "한글파일.py",
        "file with spaces.py",
        "한글폴더/내부 파일.py",
        "report (draft).py",
    ],
)
def test_status_and_stage_preserve_special_paths(tmp_path, relative_path):
    git = initialized_repo(tmp_path)
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("print('ok')", encoding="utf-8")

    assert git.changed_paths() == [relative_path]

    staged = git.stage_paths(git.changed_paths())

    assert staged.returncode == 0
    assert git.staged_paths() == [relative_path]


def test_renamed_korean_file_preserves_source_and_destination(tmp_path):
    git = initialized_repo(tmp_path)
    original = "기존 한글 문서.txt"
    renamed = "변경된 한글 문서 (최종).txt"
    (tmp_path / original).write_text("content", encoding="utf-8")
    run_git(tmp_path, "add", original)
    run_git(tmp_path, "commit", "-m", "add korean file")
    run_git(tmp_path, "mv", original, renamed)

    entries = git.status_porcelain()
    changed = git.changed_paths()

    assert len(entries) == 1
    assert entries[0].path == renamed
    assert entries[0].original_path == original
    assert changed == [renamed]
    assert git.changed_paths(include_rename_sources=True) == [renamed, original]
    assert git.stage_paths(changed).returncode == 0
    status = run_git(tmp_path, "diff", "--cached", "--name-status", "-M").stdout
    assert status.startswith("R")
    assert git.staged_paths() == [renamed]


def test_deleted_korean_file_is_staged_with_nul_pathspec(tmp_path):
    git = initialized_repo(tmp_path)
    relative_path = "한글 폴더/삭제할 파일.txt"
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("content", encoding="utf-8")
    run_git(tmp_path, "add", relative_path)
    run_git(tmp_path, "commit", "-m", "add file to delete")
    path.unlink()

    assert git.changed_paths() == [relative_path]
    assert git.stage_paths(git.changed_paths()).returncode == 0
    status = run_git(tmp_path, "diff", "--cached", "--name-status").stdout
    assert status.startswith("D")
    assert git.staged_paths() == [relative_path]


def test_sensitive_file_keeps_exact_korean_path_and_is_blocked(tmp_path):
    git = initialized_repo(tmp_path)
    relative_path = "한글 폴더/고객 자료 (최종).xlsx"
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("sensitive", encoding="utf-8")

    changed = git.changed_paths()

    assert changed == [relative_path]
    assert find_sensitive_paths(changed) == [relative_path]


def test_stage_uses_nul_pathspec_stdin_and_shell_false(tmp_path):
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "", "")

    paths = ["한글 파일.py", "폴더/이름 (최종).py"]
    GitService(tmp_path, runner=runner).stage_paths(paths)

    args, kwargs = calls[0]
    assert args == ["git", "add", "--all", "--pathspec-from-file=-", "--pathspec-file-nul"]
    assert kwargs["input"] == "한글 파일.py\0폴더/이름 (최종).py\0"
    assert kwargs["shell"] is False
