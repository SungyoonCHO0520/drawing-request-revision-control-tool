from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.team_sync.profile import load_profile, profile_for_developer, save_profile
from src.team_sync.result_models import SyncResult
from src.team_sync.sync_service import SyncService


def print_result(result: SyncResult) -> int:
    print(result.message)
    if result.branch:
        print(f"Branch: {result.branch}")
    if result.commit_id:
        print(f"Commit: {result.commit_id}")
    if result.pull_request_url:
        print(f"Pull Request: {result.pull_request_url}")
    if result.conflicts:
        print("Conflict files:")
        for path in result.conflicts:
            print(f"  - {path}")
    for detail in result.details:
        if detail:
            print(detail)
    return 0 if result.success else 1


def launch_desktop(sync_done: bool = False) -> None:
    python = Path(sys.executable)
    pythonw = python.with_name("pythonw.exe")
    executable = pythonw if pythonw.exists() else python
    environment = os.environ.copy()
    if sync_done:
        environment["PFC_TEAM_SYNC_DONE"] = "1"
    subprocess.Popen([str(executable), str(ROOT / "desktop" / "app.py")], cwd=ROOT, env=environment)


def cmd_profile(args) -> int:
    developer = args.developer
    if not developer:
        developer = "성윤" if args.branch == "sungyoon-codex" else "학석"
    profile = profile_for_developer(developer)
    save_profile(profile, ROOT)
    print(f"Saved profile: {profile.developer_name} / {profile.branch_name} / {profile.development_tool}")
    return 0


def cmd_status(_args) -> int:
    status = SyncService(ROOT).status(fetch=True)
    print(f"Developer: {status.developer_name or 'Not configured'}")
    print(f"Local branch: {status.local_branch or '-'}")
    print(f"Remote branch: {status.remote_branch or '-'}")
    print(f"Local commit: {status.local_commit or '-'}")
    print(f"Main commit: {status.main_commit or '-'}")
    print(f"Local changes: {'Yes' if status.has_local_changes else 'No'}")
    print(f"State: {status.sync_state}")
    return 0


def cmd_launch_sync(args) -> int:
    if load_profile(ROOT) is None:
        print("Developer profile is not configured. The app will ask you to select one.")
        if args.launch:
            launch_desktop(sync_done=False)
        return 0
    result = SyncService(ROOT).ensure_startup_sync()
    code = print_result(result)
    if result.success and args.launch:
        launch_desktop(sync_done=True)
    return code


def cmd_publish(args) -> int:
    message = args.message or input("Commit message: ").strip()
    if not message:
        print("Commit message is required.")
        return 1
    return print_result(SyncService(ROOT).upload_my_work(message))


def cmd_integrate(_args) -> int:
    return print_result(SyncService(ROOT).integrate_my_work())


def cmd_sync_main(args) -> int:
    return print_result(SyncService(ROOT).apply_main_changes(run_tests=args.test))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PFC IN Team Sync CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    profile = sub.add_parser("profile", help="Save the local developer profile")
    profile_group = profile.add_mutually_exclusive_group(required=True)
    profile_group.add_argument("--developer", choices=["성윤", "학석"])
    profile_group.add_argument("--branch", choices=["sungyoon-codex", "hakseok-claude"])
    profile.set_defaults(func=cmd_profile)

    status = sub.add_parser("status", help="Show local and remote sync status")
    status.set_defaults(func=cmd_status)

    launch = sub.add_parser("launch-sync", help="Safely sync main and optionally launch the app")
    launch.add_argument("--launch", action="store_true")
    launch.set_defaults(func=cmd_launch_sync)

    publish = sub.add_parser("publish", help="Test, commit, and push to the personal branch")
    publish.add_argument("--message")
    publish.set_defaults(func=cmd_publish)

    integrate = sub.add_parser("integrate", help="Create and merge a pull request into main")
    integrate.set_defaults(func=cmd_integrate)

    sync_main = sub.add_parser("sync-main", help="Merge origin/main into the personal branch")
    sync_main.add_argument("--test", action="store_true")
    sync_main.set_defaults(func=cmd_sync_main)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
