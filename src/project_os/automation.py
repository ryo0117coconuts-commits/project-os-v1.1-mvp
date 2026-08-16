from __future__ import annotations

from .core import ContractError, ConfigLoader, EventRecorder


class Authority:
    def __init__(self, config: ConfigLoader):
        self.permissions = config.load("permissions.yaml")["permissions"]

    def check(self, role: str, action: str) -> bool:
        denied = self.permissions.get(role, {}).get("denied", [])
        return action not in denied

    def require(self, role: str, action: str):
        if not self.check(role, action):
            raise ContractError(f"Authority denied: {role} cannot {action}")


class AutomationEngine:
    def __init__(self, config: ConfigLoader, authority: Authority, events: EventRecorder | None = None):
        self.config = config
        self.authority = authority
        self.events = events or EventRecorder()
        self.definitions = config.load("automation.yaml")["automations"]

    def run(self, automation_id: str, context: dict):
        definition = self.definitions.get(automation_id, {"name": "Unknown"})
        try:
            if automation_id not in self.definitions:
                raise ContractError(f"Unknown automation: {automation_id}")
            if automation_id == "AUTO-001":
                result = {"status": "PASS", "classification": "lifecycle_validated"}
            elif automation_id == "AUTO-002":
                missing = context.get("missing_required", [])
                result = {"status": "PASS" if not missing else "WARNING", "missing": missing}
            elif automation_id == "AUTO-003":
                critical = bool(context.get("critical_issue"))
                result = {"status": "BLOCKER CANDIDATE" if critical else "PASS", "escalate": critical}
            else:
                raise ContractError("Unsupported configured automation")
        except Exception as exc:
            result = {"status": "FAIL", "fallback": "MANUAL", "error": str(exc)}
        self.events.record("AUTOMATION", automation_id=automation_id, definition=definition, result=result)
        return result
