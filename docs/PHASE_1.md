# NEXUS-X Phase 1 — Intelligence

## Implemented

### 1. Real Copilot
- Uses OpenAI Responses API when `OPENAI_API_KEY` is configured.
- Uses live project context: tasks, risks, dependencies, health and critical path.
- Uses WHY / EVIDENCE / IMPACT / ACTION framing for project decisions.
- Has a deterministic local fallback for common project/coding/explanation questions.

### 2. Analyzer 2.0
- Natural-language extraction of deadline, team size, scope, requirements, tasks, effort, owners, dependencies and risks.
- Optional LLM extraction when an API key is configured.
- Deterministic calculations are applied after extraction so downstream numbers are data-driven.

### 3. Real Critical Path
- Topological ordering.
- Earliest start/finish.
- Latest start/finish.
- Slack.
- Critical path.
- Circular dependency detection.

### 4. Real Health Engine
Health is calculated from:
- effort-weighted progress
- schedule pressure
- risk pressure
- blocked work
- critical-path pressure
- team workload

The API returns the component scores and human-readable reasons.

## Verification in the user's environment

Run:

```powershell
pip install -r requirements.txt
python -m pytest -q
python -m backend.app
```

The build environment used to prepare this package does not contain Flask, so the full suite must be run in the user's configured Python environment.
