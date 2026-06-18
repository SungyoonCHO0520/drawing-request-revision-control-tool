from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


class GitService:
    def __init__(self, project_root: str | Path, runner=None):
        self.project_root = Path(project_root)
        self.runner = runner or subprocess.run

    def command_available(self, command: str) -> bool:
        return shutil.which(command) is not None

    def run(self, args: Sequence[str], check: bool = False) -> subprocess.CompletedProcess:
        result = self.runner(
            list(args),
            cwd=self.project_root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if check and result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Command failed")
        return result

    def git(self, *args: str, check: bool = False) -> subprocess.CompletedProcess:
        return self.run(["git", *args], check=check)

    def fetch(self) -> subprocess.CompletedProcess:
        return self.git("fetch", "origin")

    def current_branch(self) -> str:
        result = self.git("branch", "--show-current")
        return result.stdout.strip() if result.returncode == 0 else ""

    def status_porcelain(self) -> list[str]:
        result = self.git("status", "--porcelain")
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]

    def changed_paths(self) -> list[str]:
        paths: list[str] = []
        for line in self.status_porcelain():
            value = line[3:] if len(line) > 3 else ""
            if " -> " in value:
                value = value.split(" -> ", 1)[1]
            if value:
                paths.append(value.strip().strip('"'))
        return paths

    def has_local_changes(self) -> bool:
        return bool(self.status_porcelain())

    def local_branch_exists(self, branch: str) -> bool:
        return self.git("show-ref", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0

    def remote_branch_exists(self, branch: str) -> bool:
        return self.git("show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}").returncode == 0

    def switch(self, branch: str) -> subprocess.CompletedProcess:
        return self.git("switch", branch)

    def create_tracking_branch(self, branch: str) -> subprocess.CompletedProcess:
        return self.git("switch", "--track", "-c", branch, f"origin/{branch}")

    def create_branch_from_main(self, branch: str) -> subprocess.CompletedProcess:
        return self.git("switch", "-c", branch, "origin/main")

    def ensure_personal_branch(self, branch: str) -> subprocess.CompletedProcess:
        if self.local_branch_exists(branch):
            return self.switch(branch)
        if self.remote_branch_exists(branch):
            return self.create_tracking_branch(branch)
        created = self.create_branch_from_main(branch)
        if created.returncode != 0:
            return created
        return self.push(branch, set_upstream=True)

    def rev_parse(self, ref: str = "HEAD") -> str:
        result = self.git("rev-parse", ref)
        return result.stdout.strip() if result.returncode == 0 else ""

    def remote_url(self) -> str:
        result = self.git("remote", "get-url", "origin")
        return result.stdout.strip() if result.returncode == 0 else ""

    def is_ancestor(self, ancestor: str, descendant: str = "HEAD") -> bool:
        return self.git("merge-base", "--is-ancestor", ancestor, descendant).returncode == 0

    def merge(self, ref: str) -> subprocess.CompletedProcess:
        return self.git("merge", "--no-edit", ref)

    def conflict_files(self) -> list[str]:
        result = self.git("diff", "--name-only", "--diff-filter=U")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def stage_paths(self, paths: list[str]) -> subprocess.CompletedProcess:
        return self.git("add", "--", *paths)

    def staged_paths(self) -> list[str]:
        result = self.git("diff", "--cached", "--name-only")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def commit(self, message: str) -> subprocess.CompletedProcess:
        return self.git("commit", "-m", message)

    def push(self, branch: str, set_upstream: bool = False) -> subprocess.CompletedProcess:
        args = ["push"]
        if set_upstream:
            args.append("-u")
        args.extend(["origin", branch])
        return self.git(*args)

    def ahead_of_remote(self, branch: str) -> bool:
        result = self.git("rev-list", "--count", f"origin/{branch}..{branch}")
        try:
            return int(result.stdout.strip()) > 0
        except ValueError:
            return False

    def run_tests(self) -> subprocess.CompletedProcess:
        return self.run([sys.executable, "-m", "pytest"])

    def install_requirements(self) -> subprocess.CompletedProcess:
        return self.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    def changed_files_between(self, old_ref: str, new_ref: str) -> list[str]:
        result = self.git("diff", "--name-only", old_ref, new_ref)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
