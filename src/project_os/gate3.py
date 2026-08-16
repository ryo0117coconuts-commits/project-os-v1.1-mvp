from __future__ import annotations

from .automation import AutomationEngine


class Gate3:
    def __init__(self, automation: AutomationEngine):
        self.automation = automation

    def check(self, *, evidence: bool, qa: bool, approval: bool, critical_issue: bool):
        checks = {
            "Required Evidence": evidence,
            "Required QA": qa,
            "Required Approval": approval,
            "Critical Issue": not critical_issue,
        }
        if critical_issue:
            result = "BLOCKER CANDIDATE"
        elif all(checks.values()):
            result = "PASS"
        else:
            result = "WARNING"
        automation_result = self.automation.run("AUTO-003", {"critical_issue": critical_issue})
        return {"result": result, "checks": checks, "automation": automation_result, "authority_action": "ESCALATE" if critical_issue else "NONE"}
