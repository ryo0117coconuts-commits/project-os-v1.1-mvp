import json
import tempfile
import unittest
from pathlib import Path

from project_os import (
    Authority, AutomationEngine, ConfigLoader, ContractError, EventRecorder,
    Gate3, IDGenerator, KDS, Lifecycle, Orchestrator, SchemaLoader, Validator,
)

ROOT = Path(__file__).resolve().parents[1]


class MVPTests(unittest.TestCase):
    def setUp(self):
        self.config = ConfigLoader(ROOT / "config")
        self.events = EventRecorder()
        self.schemas = SchemaLoader(ROOT / "schemas")
        self.validator = Validator(self.schemas)
        self.authority = Authority(self.config)
        self.automation = AutomationEngine(self.config, self.authority, self.events)
        self.lifecycle = Lifecycle(self.config, self.events)

    def test_schemas_parse_and_required_validation(self):
        for name in ["project.schema.json", "lifecycle.schema.json", "decision.schema.json", "evidence.schema.json", "knowledge.schema.json"]:
            data = json.loads((ROOT / "schemas" / name).read_text())
            self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.validator.validate("project.schema.json", {"project_id": "P-1", "name": "x", "state": "PROPOSED"})
        with self.assertRaises(ContractError):
            self.validator.validate("project.schema.json", {"project_id": "P-1"})

    def test_config_driven_lifecycle(self):
        project = {"project_id": "P-1", "name": "Golden", "state": "PROPOSED"}
        for target in ["DEFINED", "VALIDATED", "ACTIVE"]:
            self.lifecycle.transition(project, target)
        self.assertEqual(project["state"], "ACTIVE")
        self.config._cache["lifecycle.yaml"]["transitions"]["ACTIVE"].remove("TASK")
        with self.assertRaises(ContractError):
            self.lifecycle.transition(project, "TASK")

    def test_golden_path(self):
        project = {"project_id": "P-GOLD", "name": "Golden", "state": "PROPOSED"}
        path = ["DEFINED", "VALIDATED", "ACTIVE", "TASK", "EVIDENCE", "GATE", "DECISION", "COMPLETED", "KDS", "CLEANUP", "ARCHIVED"]
        for target in path[:-1]:
            self.lifecycle.transition(project, target)
        self.lifecycle.archive(project)
        self.assertEqual(project["state"], "ARCHIVED")

    def test_stalled_recovery(self):
        project = {"project_id": "P-STALLED", "name": "Stalled", "state": "ACTIVE"}
        self.lifecycle.transition(project, "STALLED")
        self.lifecycle.reopen_review(project)
        self.assertEqual(project["state"], "ACTIVE")

    def test_kill_path(self):
        project = {"project_id": "P-KILL", "name": "Kill", "state": "ACTIVE"}
        for target in ["KILLED", "KDS", "CLEANUP"]:
            self.lifecycle.transition(project, target)
        self.lifecycle.archive(project)
        self.assertEqual(project["state"], "ARCHIVED")

    def test_pivot_path(self):
        project = {"project_id": "P-PIVOT", "name": "Pivot", "state": "ACTIVE"}
        self.lifecycle.transition(project, "PIVOTED")
        self.lifecycle.transition(project, "DEFINED")
        self.assertEqual(project["state"], "DEFINED")

    def test_kds_traceability(self):
        kds = KDS(self.validator, IDGenerator())
        d = kds.add("DECISION", "Decision recorded")
        e = kds.add("EVIDENCE", "Evidence recorded")
        l = kds.add("LEARNING", "Learning recorded", [d["knowledge_id"], e["knowledge_id"]])
        self.assertTrue(kds.trace(d["knowledge_id"], e["knowledge_id"], l["knowledge_id"]))

    def test_gate3(self):
        gate = Gate3(self.automation)
        self.assertEqual(gate.check(evidence=True, qa=True, approval=True, critical_issue=False)["result"], "PASS")
        self.assertEqual(gate.check(evidence=True, qa=True, approval=True, critical_issue=True)["result"], "BLOCKER CANDIDATE")
        self.assertEqual(gate.check(evidence=False, qa=True, approval=True, critical_issue=False)["result"], "WARNING")

    def test_authority_denies_os_rule_change(self):
        orchestrator = Orchestrator(self.authority)
        with self.assertRaises(ContractError):
            orchestrator.attempt_os_rule_change()

    def test_orchestrator_output(self):
        orchestrator = Orchestrator(self.authority)
        result = orchestrator.dispatch(
            {"need": "Validate evidence", "priority": "P0", "reason": "Gate pending", "success_condition": "Evidence passes", "authority_required": False},
            [], [], ["QA"], []
        )
        self.assertEqual(set(result), {"action", "owner", "priority", "reason", "success_condition", "authority_required"})
        self.assertEqual(result["owner"], "QA")

    def test_automation_failure_falls_back_to_manual(self):
        result = self.automation.run("AUTO-UNKNOWN", {})
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["fallback"], "MANUAL")

    def test_cleanup_retention(self):
        kds = KDS(self.validator)
        artifacts = [
            {"name": "temp", "retention": "REMOVE"},
            {"name": "decision", "retention": "RETAIN"},
            {"name": "lifecycle", "retention": "RETAIN"},
            {"name": "evidence", "retention": "RETAIN"},
            {"name": "learning", "retention": "RETAIN"},
        ]
        kept = kds.cleanup(artifacts)
        self.assertEqual([x["name"] for x in kept], ["decision", "lifecycle", "evidence", "learning"])


if __name__ == "__main__":
    unittest.main()
