# Project OS v1.1 MVP

Repository implementation of the Project OS v1.1 MVP Implementation Contract.

## Golden Path

`PROPOSED → DEFINED → VALIDATED → ACTIVE → TASK → EVIDENCE → GATE → DECISION → COMPLETED → KDS → CLEANUP → ARCHIVED`

Failure paths supported by the contract:

- `ACTIVE → STALLED → ACTIVE`
- `ACTIVE → KILLED → KDS → ARCHIVED`
- `ACTIVE → PIVOTED → DEFINED`

## Repository Structure

```text
README.md
PROJECT_OS_SPEC.md
schemas/
config/
prompts/
src/project_os/
tests/
```

## Build / Test

Requires Python 3.11+ and PyYAML. Run:

```bash
python -m unittest discover -s tests -v
```

## Authority Boundary

The implementation validates authority but does not grant OS-rule-change authority to the Orchestrator. Authority failures are escalated rather than converted into automatic BLOCKER decisions.
