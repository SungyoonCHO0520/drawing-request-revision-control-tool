from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SyncResult:
    success: bool
    message: str
    details: list[str] = field(default_factory=list)
    branch: str = ""
    commit_id: str = ""
    pull_request_url: str = ""
    conflicts: list[str] = field(default_factory=list)


@dataclass
class SyncStatus:
    developer_name: str = ""
    local_branch: str = ""
    remote_branch: str = ""
    local_commit: str = ""
    main_commit: str = ""
    has_local_changes: bool = False
    update_available: bool = False
    sync_state: str = "Not checked"
    last_sync_at: str = ""

