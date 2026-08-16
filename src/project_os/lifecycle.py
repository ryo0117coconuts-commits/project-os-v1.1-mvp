from __future__ import annotations

from dataclasses import dataclass

from .core import ContractError, ConfigLoader, EventRecorder


@dataclass
class LifecycleRecord:
    project_id: str
    previous_state: str
    state: str
    reason: str = ""


class Lifecycle:
    def __init__(self, config: ConfigLoader, events: EventRecorder | None = None):
        self.transitions = config.load("lifecycle.yaml")["transitions"]
        self.events = events or EventRecorder()

    def transition(self, project: dict, target: str, reason: str = "") -> LifecycleRecord:
        current = project["state"]
        allowed = self.transitions.get(current, [])
        if target not in allowed:
            raise ContractError(f"Invalid transition: {current} -> {target}")
        project["state"] = target
        record = LifecycleRecord(project["project_id"], current, target, reason)
        self.events.record("LIFECYCLE", project_id=record.project_id, previous_state=current, state=target, reason=reason)
        return record

    def archive(self, project: dict):
        if project["state"] != "CLEANUP":
            raise ContractError("Archive requires CLEANUP state")
        return self.transition(project, "ARCHIVED", "cleanup complete")

    def reopen_review(self, project: dict):
        if project["state"] != "STALLED":
            raise ContractError("Reopen Review requires STALLED state")
        return self.transition(project, "ACTIVE", "reopen review")
