# NEXUS-X Phase 2 — Project Intelligence

- Live risk engine recalculates severity/score from current tasks, dependencies, blockers, schedule and capacity.
- Dependency impact endpoint exposes downstream pressure and critical-path involvement.
- What-If now rebuilds the critical path, risk set and health score for the scenario.
- Scenarios are persisted and retrievable.
- Project state recalculates health, risk and critical path after task/dependency changes.

This phase is intentionally local-first. Cloud, billing, SSO and real IoT remain later production layers.
