from __future__ import annotations

from .core import ContractError, IDGenerator, Validator


class KDS:
    def __init__(self, validator: Validator, ids: IDGenerator | None = None):
        self.validator = validator
        self.ids = ids or IDGenerator()
        self.records: list[dict] = []

    def add(self, record_type: str, content: str, references: list[str] | None = None):
        prefix = record_type.upper()
        record = {
            "knowledge_id": self.ids.generate(prefix),
            "type": record_type.upper(),
            "content": content,
            "references": references or [],
        }
        self.validator.validate("knowledge.schema.json", record)
        self.records.append(record)
        return record

    def trace(self, decision_id: str, evidence_id: str, learning_id: str):
        ids = {r["knowledge_id"] for r in self.records}
        required = {decision_id, evidence_id, learning_id}
        if not required.issubset(ids):
            raise ContractError("Decision -> Evidence -> Learning traceability is incomplete")
        return True

    def cleanup(self, artifacts: list[dict]):
        return [a for a in artifacts if a.get("retention") == "RETAIN"]
