# NEXUS-X Phase 1 Architecture

```text
Browser
  |
  v
Flask API
  |
  +-- Analyzer 2.0
  |     +-- optional OpenAI extraction
  |     +-- deterministic normalization
  |
  +-- Critical Path Engine
  |     +-- dependency graph
  |     +-- topological sort
  |     +-- ES/EF/LS/LF
  |     +-- slack
  |     +-- cycle detection
  |
  +-- Health Engine
  |     +-- progress
  |     +-- schedule
  |     +-- risk
  |     +-- blockers
  |     +-- critical path
  |     +-- workload
  |
  +-- Project-aware Copilot
  |     +-- OpenAI Responses API
  |     +-- deterministic fallback
  |
  +-- SQLite persistence
```

Every project read recalculates the critical path and health from stored tasks, dependencies, risks and team data.
