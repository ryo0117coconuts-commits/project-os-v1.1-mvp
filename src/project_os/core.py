from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import yaml
from jsonschema import Draft202012Validator, RefResolver


ROOT = Path(__file__).resolve().parents[2]


class ContractError(Exception):
    pass


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class SchemaLoader:
    def __init__(self, schema_dir: Path | None = None):
        self.schema_dir = schema_dir or ROOT / "schemas"
        self._schemas = {}

    def load(self, name: str):
        if name not in self._schemas:
            self._schemas[name] = load_json(self.schema_dir / name)
        return self._schemas[name]

    def validator(self, name: str):
        schema = self.load(name)
        resolver = RefResolver((self.schema_dir / name).as_uri(), schema)
        return Draft202012Validator(schema, resolver=resolver)


class ConfigLoader:
    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or ROOT / "config"
        self._cache = {}

    def load(self, name: str):
        if name not in self._cache:
            self._cache[name] = load_yaml(self.config_dir / name)
        return self._cache[name]


class IDGenerator:
    def generate(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"


class Validator:
    def __init__(self, schemas: SchemaLoader):
        self.schemas = schemas

    def validate(self, schema_name: str, instance: dict) -> None:
        errors = sorted(self.schemas.validator(schema_name).iter_errors(instance), key=lambda e: list(e.path))
        if errors:
            detail = "; ".join(error.message for error in errors)
            raise ContractError(detail)


class EventRecorder:
    def __init__(self):
        self.events: list[dict] = []

    def record(self, event_type: str, **payload):
        event = {"event_type": event_type, **payload}
        self.events.append(event)
        return event
