from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .git_service import GitService
from .github_service import GitHubService
from .profile import PROJECT_ROOT, TeamProfile, load_profile, save_profile
from .result_models import SyncResult, SyncStatus
from .security_check import find_sensitive_paths


LOCAL_CHANGE_MESSAGE = (
    "로컬 수정사항이 있어 Main 자동 반영을 건너뜁니다. "
    "'내 작업 Main 통합'을 실행하면 별도 업로드 없이 로컬 작업을 Commit한 뒤 최신 Main과 통합합니다."
)


def _now_text() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


class SyncService:
    def __init__(
        self,
        project_root: str | Path = PROJECT_ROOT,
        git_service: GitService | None = None,
        github_service: GitHubService | None = None,
    ):
        self.project_root = Path(project_root)
        self.git = git_service or GitService(self.project_root)
        self.github = github_service or GitHubService(self.project_root)

    def profile(self) -> TeamProfile | None:
        return load_profile(self.project_root)

    def _save_sync(self, profile: TeamProfile, main_commit: str = "") -> None:
        if main_commit:
            profile.last_main_commit = main_commit
        profile.last_sync_at = _now_text()
        save_profile(profile, self.project_root)

    def status(self, fetch: bool = False) -> SyncStatus:
        profile = self.profile()
        if profile is None:
            return SyncStatus(sync_state="Developer profile is not configured")
        fetch_message = ""
        if fetch:
            fetched = self.git.fetch()
            if fetched.returncode != 0:
                fetch_message = "Remote fetch failed"
        local_commit = self.git.rev_parse("HEAD")
        main_commit = self.git.rev_parse("origin/main")
        update_available = bool(main_commit and not self.git.is_ancestor("origin/main", "HEAD"))
        state = fetch_message or ("Main update available" if update_available else "Up to date")
        return SyncStatus(
            developer_name=profile.developer_name,
            local_branch=self.git.current_branch(),
            remote_branch=f"origin/{profile.branch_name}",
            local_commit=local_commit,
            main_commit=main_commit,
            has_local_changes=self.git.has_local_changes(),
            update_available=update_available,
            sync_state=state,
            last_sync_at=profile.last_sync_at,
        )

    def ensure_startup_sync(self) -> SyncResult:
        profile = self.profile()
        if profile is None:
            return SyncResult(False, "개발자 프로필을 먼저 선택하세요.")
        if not self.git.command_available("git"):
            return SyncResult(False, "Git이 설치되어 있지 않거나 PATH에서 찾을 수 없습니다.")
        if self.git.current_branch() == "main" and self.git.has_local_changes():
            return SyncResult(
                False,
                "main 브랜치에 로컬 수정사항이 있습니다. 개인 브랜치로 옮겨 Commit한 후 다시 실행하세요.",
            )
        fetched = self.git.fetch()
        if fetched.returncode != 0:
            return SyncResult(False, "GitHub 원격 정보를 가져오지 못했습니다.", [fetched.stderr.strip()])
        switched = self.git.ensure_personal_branch(profile.branch_name)
        if switched.returncode != 0:
            return SyncResult(False, f"개인 브랜치 {profile.branch_name}(으)로 전환하지 못했습니다.", [switched.stderr.strip()])
        if self.git.has_local_changes():
            return SyncResult(True, LOCAL_CHANGE_MESSAGE, branch=profile.branch_name)
        old_head = self.git.rev_parse("HEAD")
        merged = self.git.merge("origin/main")
        if merged.returncode != 0:
            conflicts = self.git.conflict_files()
            return SyncResult(False, "Main 자동 반영 중 충돌이 발생했습니다.", [merged.stderr.strip()], conflicts=conflicts)
        new_head = self.git.rev_parse("HEAD")
        changed = self.git.changed_files_between(old_head, new_head) if old_head and new_head and old_head != new_head else []
        if "requirements.txt" in changed:
            installed = self.git.install_requirements()
            if installed.returncode != 0:
                return SyncResult(False, "Main은 반영됐지만 requirements 설치에 실패했습니다.", [installed.stderr.strip()])
        main_commit = self.git.rev_parse("origin/main")
        self._save_sync(profile, main_commit)
        return SyncResult(True, "최신 Main 내용을 개인 브랜치에 안전하게 반영했습니다.", branch=profile.branch_name, commit_id=new_head)

    def check_main_updates(self, apply_if_enabled: bool = False) -> SyncResult:
        profile = self.profile()
        if profile is None:
            return SyncResult(False, "개발자 프로필을 먼저 선택하세요.")
        fetched = self.git.fetch()
        if fetched.returncode != 0:
            return SyncResult(False, "GitHub main 확인에 실패했습니다.", [fetched.stderr.strip()])
        main_commit = self.git.rev_parse("origin/main")
        has_update = bool(main_commit and not self.git.is_ancestor("origin/main", "HEAD"))
        profile.last_main_commit = main_commit
        save_profile(profile, self.project_root)
        if not has_update:
            return SyncResult(True, "현재 개인 브랜치에 최신 Main이 반영되어 있습니다.", commit_id=main_commit)
        if apply_if_enabled and profile.auto_merge:
            return self.apply_main_changes()
        return SyncResult(True, "새로운 Main 업데이트가 있습니다.", commit_id=main_commit)

    def apply_main_changes(self, run_tests: bool = False) -> SyncResult:
        profile = self.profile()
        if profile is None:
            return SyncResult(False, "개발자 프로필을 먼저 선택하세요.")
        if self.git.current_branch() != profile.branch_name:
            return SyncResult(False, f"현재 브랜치가 개인 브랜치({profile.branch_name})가 아닙니다.")
        if self.git.has_local_changes():
            return SyncResult(False, LOCAL_CHANGE_MESSAGE)
        fetched = self.git.fetch()
        if fetched.returncode != 0:
            return SyncResult(False, "GitHub main 확인에 실패했습니다.", [fetched.stderr.strip()])
        old_head = self.git.rev_parse("HEAD")
        merged = self.git.merge("origin/main")
        if merged.returncode != 0:
            conflicts = self.git.conflict_files()
            return SyncResult(False, "Main 변경사항 반영 중 충돌이 발생했습니다.", [merged.stderr.strip()], conflicts=conflicts)
        new_head = self.git.rev_parse("HEAD")
        changed = self.git.changed_files_between(old_head, new_head) if old_head and new_head and old_head != new_head else []
        if "requirements.txt" in changed:
            installed = self.git.install_requirements()
            if installed.returncode != 0:
                return SyncResult(False, "Main은 반영됐지만 requirements 설치에 실패했습니다.", [installed.stderr.strip()])
        if run_tests:
            tested = self.git.run_tests()
            if tested.returncode != 0:
                return SyncResult(False, "Main 반영 후 테스트가 실패했습니다.", [tested.stdout[-3000:], tested.stderr[-1000:]])
        main_commit = self.git.rev_parse("origin/main")
        self._save_sync(profile, main_commit)
        return SyncResult(True, "Main 변경사항 반영이 완료되었습니다.", branch=profile.branch_name, commit_id=new_head)

    def upload_my_work(self, commit_message: str) -> SyncResult:
        profile = self.profile()
        if profile is None:
            return SyncResult(False, "개발자 프로필을 먼저 선택하세요.")
        branch = self.git.current_branch()
        if branch != profile.branch_name:
            return SyncResult(False, f"현재 브랜치가 개인 브랜치({profile.branch_name})가 아닙니다.", branch=branch)
        tested = self.git.run_tests()
        if tested.returncode != 0:
            return SyncResult(False, "테스트가 실패하여 Commit과 Push를 중단했습니다.", [tested.stdout[-3000:], tested.stderr[-1000:]])
        changed_paths = self.git.changed_paths()
        sensitive = find_sensitive_paths(self.git.changed_paths(include_rename_sources=True))
        if sensitive:
            return SyncResult(False, "민감자료가 감지되어 Commit을 중단했습니다.", sensitive)
        if not changed_paths:
            return SyncResult(True, "Commit할 변경사항이 없습니다.", branch=branch, commit_id=self.git.rev_parse("HEAD"))
        staged = self.git.stage_paths(changed_paths)
        if staged.returncode != 0:
            details = [f"Stage 대상 파일: {path}" for path in changed_paths]
            if staged.stderr.strip():
                details.append(f"Git 오류: {staged.stderr.strip()}")
            return SyncResult(False, "변경파일 Stage에 실패했습니다.", details)
        staged_sensitive = find_sensitive_paths(self.git.staged_paths())
        if staged_sensitive:
            return SyncResult(False, "Stage에서 민감자료가 감지되어 Commit을 중단했습니다.", staged_sensitive)
        committed = self.git.commit(commit_message.strip())
        if committed.returncode != 0:
            return SyncResult(False, "Commit에 실패했습니다.", [committed.stderr.strip()])
        pushed = self.git.push(branch, set_upstream=True)
        if pushed.returncode != 0:
            return SyncResult(False, "Commit은 생성됐지만 개인 브랜치 Push에 실패했습니다.", [pushed.stderr.strip()], branch=branch)
        return SyncResult(True, "내 작업을 개인 브랜치에 업로드했습니다.", branch=branch, commit_id=self.git.rev_parse("HEAD"))

    @staticmethod
    def _checks_passed(pr: dict) -> bool:
        checks = pr.get("statusCheckRollup") or []
        for check in checks:
            conclusion = str(check.get("conclusion") or check.get("state") or "").upper()
            if conclusion not in {"SUCCESS", "SKIPPED", "NEUTRAL"}:
                return False
        return True

    def integrate_my_work(self, commit_message: str = "") -> SyncResult:
        profile = self.profile()
        if profile is None:
            return SyncResult(False, "개발자 프로필을 먼저 선택하세요.")
        branch = self.git.current_branch()
        if branch != profile.branch_name or branch == "main":
            return SyncResult(False, f"개인 브랜치({profile.branch_name})에서만 Main 통합할 수 있습니다.", branch=branch)
        if not self.git.command_available("git"):
            return SyncResult(False, "Git을 찾을 수 없습니다.")
        if not self.github.available():
            return SyncResult(False, "GitHub CLI(gh)가 설치되어 있지 않습니다.")
        if not self.github.authenticated():
            return SyncResult(False, "GitHub CLI 로그인이 필요합니다. gh auth login을 실행하세요.")
        had_local_changes = self.git.has_local_changes()
        tested = self.git.run_tests()
        if tested.returncode != 0:
            return SyncResult(False, "테스트 실패로 Main 통합을 중단했습니다.", [tested.stdout[-3000:]])
        if had_local_changes:
            changed_paths = self.git.changed_paths()
            sensitive = find_sensitive_paths(self.git.changed_paths(include_rename_sources=True))
            if sensitive:
                return SyncResult(False, "민감자료가 감지되어 Main 통합을 중단했습니다.", sensitive)
            if not changed_paths:
                return SyncResult(False, "로컬 수정파일 경로를 확인하지 못해 Main 통합을 중단했습니다.")
            staged = self.git.stage_paths(changed_paths)
            if staged.returncode != 0:
                details = [f"Stage 대상 파일: {path}" for path in changed_paths]
                if staged.stderr.strip():
                    details.append(f"Git 오류: {staged.stderr.strip()}")
                return SyncResult(False, "로컬 작업 Stage에 실패하여 Main 통합을 중단했습니다.", details)
            staged_sensitive = find_sensitive_paths(self.git.staged_paths())
            if staged_sensitive:
                return SyncResult(False, "Stage에서 민감자료가 감지되어 Main 통합을 중단했습니다.", staged_sensitive)
            message = commit_message.strip() or f"Integrate {profile.developer_name} local work"
            committed = self.git.commit(message)
            if committed.returncode != 0:
                return SyncResult(False, "로컬 작업 Commit에 실패하여 Main 통합을 중단했습니다.", [committed.stderr.strip()])
            if self.git.has_local_changes():
                return SyncResult(False, "Commit 후에도 로컬 수정사항이 남아 Main 통합을 중단했습니다.")
        fetched = self.git.fetch()
        if fetched.returncode != 0:
            return SyncResult(False, "원격 저장소 접근에 실패했습니다.", [fetched.stderr.strip()])
        merged = self.git.merge("origin/main")
        if merged.returncode != 0:
            conflicts = self.git.conflict_files()
            return SyncResult(False, "Main 선행 병합에서 충돌이 발생했습니다.", conflicts=conflicts)
        retested = self.git.run_tests()
        if retested.returncode != 0:
            return SyncResult(False, "Main 선행 병합 후 테스트가 실패했습니다.", [retested.stdout[-3000:]])
        pushed = self.git.push(branch, set_upstream=True)
        if pushed.returncode != 0:
            return SyncResult(False, "개인 브랜치 Push에 실패했습니다.", [pushed.stderr.strip()])
        pr = self.github.find_open_pull_request(branch)
        pr_url = ""
        if pr is None:
            created = self.github.create_pull_request(branch, f"Merge {branch} into main")
            if created.returncode != 0:
                return SyncResult(False, "Pull Request 생성에 실패했습니다.", [created.stderr.strip()])
            pr_url = created.stdout.strip()
        checks = self.github.wait_for_checks(branch)
        if checks.returncode != 0:
            self.github.open_pull_request(branch)
            return SyncResult(
                False,
                "GitHub Actions 검사가 실패했거나 아직 완료되지 않았습니다.",
                [checks.stdout.strip(), checks.stderr.strip()],
                pull_request_url=pr_url,
            )
        _, pr = self.github.view_pull_request(branch)
        if not pr:
            return SyncResult(False, "Pull Request 상태를 확인하지 못했습니다.", pull_request_url=pr_url)
        pr_url = str(pr.get("url") or pr_url)
        if str(pr.get("mergeable", "")).upper() != "MERGEABLE" or not self._checks_passed(pr):
            self.github.open_pull_request(branch)
            return SyncResult(False, "Pull Request 충돌 또는 GitHub 검사를 확인해야 합니다.", pull_request_url=pr_url)
        merged_pr = self.github.merge_pull_request(branch)
        if merged_pr.returncode != 0:
            self.github.open_pull_request(branch)
            return SyncResult(False, "Pull Request를 Main에 병합하지 못했습니다.", [merged_pr.stderr.strip()], pull_request_url=pr_url)
        fetched = self.git.fetch()
        if fetched.returncode != 0:
            return SyncResult(False, "Main 병합은 완료됐지만 최신 원격 정보를 가져오지 못했습니다.", pull_request_url=pr_url)
        synced = self.git.merge("origin/main")
        if synced.returncode != 0:
            return SyncResult(False, "Main 병합 후 개인 브랜치 최신화 중 충돌이 발생했습니다.", conflicts=self.git.conflict_files(), pull_request_url=pr_url)
        repushed = self.git.push(branch, set_upstream=True)
        if repushed.returncode != 0:
            return SyncResult(False, "Main은 통합됐지만 개인 브랜치 재동기화 Push에 실패했습니다.", pull_request_url=pr_url)
        main_commit = self.git.rev_parse("origin/main")
        self._save_sync(profile, main_commit)
        message = "내 작업을 Main에 통합하고 개인 브랜치를 최신화했습니다."
        if had_local_changes:
            message = "로컬 작업을 자동 Commit한 뒤 최신 Main과 통합하고 개인 브랜치를 최신화했습니다."
        return SyncResult(True, message, branch=branch, commit_id=main_commit, pull_request_url=pr_url)
