from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class GitStatusEntry:
    status: str
    path: str
    original_path: str | None = None


class GitService:
    def __init__(self, project_root: str | Path, runner=None):
        self.project_root = Path(project_root)
        self.runner = runner or subprocess.run

    def command_available(self, command: str) -> bool:
        return shutil.which(command) is not None

    def run(
        self,
        args: Sequence[str],
        check: bool = False,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess:
        result = self.runner(
            list(args),
            cwd=self.project_root,
            input=input_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            shell=False,
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

    @staticmethod
    def _parse_porcelain_v1_z(output: str) -> list[GitStatusEntry]:
        fields = output.split("\0")
        entries: list[GitStatusEntry] = []
        index = 0
        while index < len(fields):
            record = fields[index]
            index += 1
            if not record:
                continue
            if len(record) < 4 or record[2] != " ":
                continue
            status = record[:2]
            path = record[3:]
            original_path = None
            if "R" in status or "C" in status:
                if index < len(fields) and fields[index]:
                    original_path = fields[index]
                    index += 1
            entries.append(GitStatusEntry(status, path, original_path))
        return entries

    @staticmethod
    def _parse_nul_paths(output: str) -> list[str]:
        return [path for path in output.split("\0") if path]

    def status_porcelain(self) -> list[GitStatusEntry]:
        result = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all")
        if result.returncode != 0:
            return []
        return self._parse_porcelain_v1_z(result.stdout)

    def changed_paths(self, include_rename_sources: bool = False) -> list[str]:
        paths: list[str] = []
        seen: set[str] = set()
        for entry in self.status_porcelain():
            candidates = (entry.path, entry.original_path) if include_rename_sources else (entry.path,)
            for path in candidates:
                if path is not None and path not in seen:
                    seen.add(path)
                    paths.append(path)
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
        result = self.git("diff", "--name-only", "--diff-filter=U", "-z")
        return self._parse_nul_paths(result.stdout) if result.returncode == 0 else []

    def stage_paths(self, paths: list[str]) -> subprocess.CompletedProcess:
        pathspecs = "\0".join(paths) + "\0"
        return self.run(
            ["git", "add", "--all", "--pathspec-from-file=-", "--pathspec-file-nul"],
            input_text=pathspecs,
        )

    def staged_paths(self) -> list[str]:
        result = self.git("diff", "--cached", "--name-only", "-z")
        return self._parse_nul_paths(result.stdout) if result.returncode == 0 else []

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
        result = self.git("diff", "--name-only", "-z", old_ref, new_ref)
        return self._parse_nul_paths(result.stdout) if result.returncode == 0 else []
