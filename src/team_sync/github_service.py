from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class GitHubService:
    def __init__(self, project_root: str | Path, runner=None):
        self.project_root = Path(project_root)
        self.runner = runner or subprocess.run

    def available(self) -> bool:
        return shutil.which("gh") is not None

    def run(self, *args: str) -> subprocess.CompletedProcess:
        return self.runner(
            ["gh", *args],
            cwd=self.project_root,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            shell=False,
        )

    def authenticated(self) -> bool:
        return self.run("auth", "status").returncode == 0

    def find_open_pull_request(self, branch: str) -> dict | None:
        result = self.run(
            "pr",
            "list",
            "--head",
            branch,
            "--base",
            "main",
            "--state",
            "open",
            "--json",
            "number,url,mergeStateStatus",
        )
        if result.returncode != 0:
            return None
        try:
            rows = json.loads(result.stdout or "[]")
            return rows[0] if rows else None
        except (TypeError, json.JSONDecodeError):
            return None

    def create_pull_request(self, branch: str, title: str) -> subprocess.CompletedProcess:
        return self.run(
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            title,
            "--body",
            "Automated team integration after local tests passed.",
        )

    def view_pull_request(self, branch: str) -> tuple[subprocess.CompletedProcess, dict | None]:
        result = self.run("pr", "view", branch, "--json", "number,url,mergeable,mergeStateStatus,statusCheckRollup")
        if result.returncode != 0:
            return result, None
        try:
            return result, json.loads(result.stdout)
        except json.JSONDecodeError:
            return result, None

    def wait_for_checks(self, branch: str) -> subprocess.CompletedProcess:
        return self.run("pr", "checks", branch, "--watch", "--fail-fast")

    def merge_pull_request(self, branch: str) -> subprocess.CompletedProcess:
        return self.run("pr", "merge", branch, "--merge")

    def open_pull_request(self, branch: str) -> subprocess.CompletedProcess:
        return self.run("pr", "view", branch, "--web")

    def repository_url(self) -> str:
        result = self.run("repo", "view", "--json", "url", "--jq", ".url")
        return result.stdout.strip() if result.returncode == 0 else ""
