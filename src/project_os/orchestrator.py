from __future__ import annotations

from .automation import Authority


class Orchestrator:
    def __init__(self, authority: Authority):
        self.authority = authority

    def dispatch(self, context: dict, evidence: list, pending_decisions: list, teams: list, rules: list):
        need = context.get("need")
        owner = teams[0] if teams else None
        priority = context.get("priority", "P1")
        authority_required = context.get("authority_required", False)
        return {
            "action": need or "REVIEW",
            "owner": owner,
            "priority": priority,
            "reason": context.get("reason", "Project state requires action"),
            "success_condition": context.get("success_condition", "Required evidence is recorded"),
            "authority_required": authority_required,
        }

    def attempt_os_rule_change(self):
        self.authority.require("orchestrator", "change_os_rule")
