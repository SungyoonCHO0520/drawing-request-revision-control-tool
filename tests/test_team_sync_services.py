from __future__ import annotations

import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

from src.team_sync.git_service import GitService
from src.team_sync.github_service import GitHubService
from src.team_sync.profile import profile_for_developer, save_profile
from src.team_sync.sync_service import LOCAL_CHANGE_MESSAGE, SyncService


def completed(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class FakeGit:
    def __init__(self):
        self.branch = "sungyoon-codex"
        self.dirty = False
        self.update_available = False
        self.test_result = completed()
        self.merge_result = completed()
        self.changed = ["src/example.py"]
        self.staged = []
        self.merge_calls = []
        self.push_calls = []
        self.commit_messages = []

    def command_available(self, _command):
        return True

    def fetch(self):
        return completed()

    def ensure_personal_branch(self, branch):
        self.branch = branch
        return completed()

    def current_branch(self):
        return self.branch

    def has_local_changes(self):
        return self.dirty

    def status_porcelain(self):
        return [" M src/example.py"] if self.dirty else []

    def changed_paths(self, include_rename_sources=False):
        return list(self.changed)

    def rev_parse(self, ref="HEAD"):
        return "main123" if ref == "origin/main" else "head456"

    def is_ancestor(self, _ancestor, _descendant="HEAD"):
        return not self.update_available

    def merge(self, ref):
        self.merge_calls.append(ref)
        return self.merge_result

    def conflict_files(self):
        return ["desktop/main_window.py"]

    def changed_files_between(self, _old, _new):
        return []

    def install_requirements(self):
        return completed()

    def run_tests(self):
        return self.test_result

    def stage_paths(self, paths):
        self.staged = list(paths)
        return completed()

    def staged_paths(self):
        return list(self.staged)

    def commit(self, message):
        self.commit_messages.append(message)
        self.dirty = False
        return completed()

    def push(self, branch, set_upstream=False):
        self.push_calls.append((branch, set_upstream))
        return completed()

    def remote_url(self):
        return "https://github.com/example/repo.git"


class FakeGitHub:
    def __init__(self):
        self.created = []
        self.merged = []
        self.opened = []
        self.check_result = completed(stdout="All checks passed")

    def available(self):
        return True

    def authenticated(self):
        return True

    def find_open_pull_request(self, _branch):
        return None

    def create_pull_request(self, branch, title):
        self.created.append((branch, title))
        return completed(stdout="https://github.com/example/repo/pull/1")

    def view_pull_request(self, _branch):
        return completed(), {
            "url": "https://github.com/example/repo/pull/1",
            "mergeable": "MERGEABLE",
            "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        }

    def wait_for_checks(self, _branch):
        return self.check_result

    def merge_pull_request(self, branch):
        self.merged.append(branch)
        return completed()

    def open_pull_request(self, branch):
        self.opened.append(branch)
        return completed()


def service(tmp_path, git=None, github=None):
    save_profile(profile_for_developer("성윤"), tmp_path)
    return SyncService(tmp_path, git_service=git or FakeGit(), github_service=github or FakeGitHub())


def test_personal_branch_is_created_from_main_when_missing(tmp_path):
    git = GitService(tmp_path)
    git.local_branch_exists = Mock(return_value=False)
    git.remote_branch_exists = Mock(return_value=False)
    git.create_branch_from_main = Mock(return_value=completed())
    git.push = Mock(return_value=completed())

    result = git.ensure_personal_branch("sungyoon-codex")

    assert result.returncode == 0
    git.create_branch_from_main.assert_called_once_with("sungyoon-codex")
    git.push.assert_called_once_with("sungyoon-codex", set_upstream=True)


def test_main_update_is_detected(tmp_path):
    git = FakeGit()
    git.update_available = True

    result = service(tmp_path, git).check_main_updates()

    assert result.success is True
    assert "새로운 Main 업데이트" in result.message


def test_clean_worktree_merges_main(tmp_path):
    git = FakeGit()

    result = service(tmp_path, git).apply_main_changes()

    assert result.success is True
    assert git.merge_calls == ["origin/main"]


def test_local_changes_stop_automatic_main_merge(tmp_path):
    git = FakeGit()
    git.dirty = True

    result = service(tmp_path, git).apply_main_changes()

    assert result.success is False
    assert result.message == LOCAL_CHANGE_MESSAGE
    assert git.merge_calls == []


def test_startup_with_local_changes_switches_branch_but_skips_merge(tmp_path):
    git = FakeGit()
    git.dirty = True

    result = service(tmp_path, git).ensure_startup_sync()

    assert result.success is True
    assert result.message == LOCAL_CHANGE_MESSAGE
    assert git.branch == "sungyoon-codex"
    assert git.merge_calls == []


def test_startup_stops_when_main_contains_local_changes(tmp_path):
    git = FakeGit()
    git.branch = "main"
    git.dirty = True

    result = service(tmp_path, git).ensure_startup_sync()

    assert result.success is False
    assert "main 브랜치" in result.message
    assert git.branch == "main"
    assert git.merge_calls == []


def test_failed_tests_stop_upload_before_stage_and_push(tmp_path):
    git = FakeGit()
    git.test_result = completed(returncode=1, stdout="failed")

    result = service(tmp_path, git).upload_my_work("test commit")

    assert result.success is False
    assert git.staged == []
    assert git.push_calls == []


def test_sensitive_file_stops_upload(tmp_path):
    git = FakeGit()
    git.changed = ["src/example.py", "company/customer_drawing.pdf"]

    result = service(tmp_path, git).upload_my_work("test commit")

    assert result.success is False
    assert "customer_drawing.pdf" in " ".join(result.details)
    assert git.push_calls == []


def test_stage_failure_lists_exact_problem_paths(tmp_path):
    git = FakeGit()
    git.changed = ["한글 폴더/작업 파일 (최종).py"]
    git.stage_paths = Mock(return_value=completed(returncode=1, stderr="stage failed"))

    result = service(tmp_path, git).upload_my_work("test commit")

    assert result.success is False
    assert "Stage 대상 파일: 한글 폴더/작업 파일 (최종).py" in result.details
    assert "Git 오류: stage failed" in result.details


def test_merge_conflict_stops_main_integration(tmp_path):
    git = FakeGit()
    git.merge_result = completed(returncode=1, stderr="conflict")
    github = FakeGitHub()

    result = service(tmp_path, git, github).integrate_my_work()

    assert result.success is False
    assert result.conflicts == ["desktop/main_window.py"]
    assert github.created == []
    assert github.merged == []


def test_successful_integration_creates_pr_and_refreshes_personal_branch(tmp_path):
    git = FakeGit()
    github = FakeGitHub()

    result = service(tmp_path, git, github).integrate_my_work()

    assert result.success is True
    assert github.created == [("sungyoon-codex", "Merge sungyoon-codex into main")]
    assert github.merged == ["sungyoon-codex"]
    assert git.merge_calls == ["origin/main", "origin/main"]
    assert len(git.push_calls) == 2


def test_integration_commits_local_changes_without_separate_upload(tmp_path):
    git = FakeGit()
    git.dirty = True
    git.changed = ["src/한글 작업 (최종).py"]
    github = FakeGitHub()

    result = service(tmp_path, git, github).integrate_my_work()

    assert result.success is True
    assert "자동 Commit" in result.message
    assert git.staged == ["src/한글 작업 (최종).py"]
    assert git.commit_messages == ["Integrate 성윤 local work"]
    assert git.merge_calls == ["origin/main", "origin/main"]
    assert github.merged == ["sungyoon-codex"]


def test_sensitive_local_file_stops_direct_main_integration(tmp_path):
    git = FakeGit()
    git.dirty = True
    git.changed = ["src/example.py", "회사 자료/검사 결과.xlsx"]
    github = FakeGitHub()

    result = service(tmp_path, git, github).integrate_my_work()

    assert result.success is False
    assert "민감자료" in result.message
    assert "회사 자료/검사 결과.xlsx" in result.details
    assert git.staged == []
    assert git.commit_messages == []
    assert git.merge_calls == []
    assert github.merged == []


def test_failed_github_checks_stop_pr_merge(tmp_path):
    git = FakeGit()
    github = FakeGitHub()
    github.check_result = completed(returncode=1, stdout="test failed")

    result = service(tmp_path, git, github).integrate_my_work()

    assert result.success is False
    assert github.merged == []
    assert github.opened == ["sungyoon-codex"]


def test_github_pr_create_uses_personal_branch_and_main(tmp_path):
    calls = []

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return completed(stdout="https://github.com/example/repo/pull/1")

    github = GitHubService(tmp_path, runner=runner)
    github.create_pull_request("hakseok-claude", "Merge work")

    args, kwargs = calls[0]
    assert args[:6] == ["gh", "pr", "create", "--base", "main", "--head"]
    assert "hakseok-claude" in args
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["shell"] is False
