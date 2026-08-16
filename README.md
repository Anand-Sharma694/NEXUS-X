# NEXUS-X — AI Project Decision & Operational Intelligence

NEXUS-X turns messy project descriptions into structured execution plans, calculates critical paths and health, continuously recalculates risk, compares What-If scenarios, recommends team members, and provides a project-aware AI Copilot.

## Final build capabilities
- AI Analyzer 2.0 + OpenAI/local fallback
- Authentication + RBAC + project isolation + CSRF
- Critical Path + dependency cycle detection
- Health and live Risk Engines
- Team skills/availability/workload + AI recommendation
- Task editing and manager-only planning controls
- Budget-aware What-If simulation and cost model
- Notifications + activity history
- Historical analytics snapshots
- Copilot with project context
- PDF/CSV reporting
- Builder 2.0 complete-runtime generation
- Responsive UI and security hardening

## Run on Windows

```powershell
pip install -r requirements.txt
python -m pytest -q
python -m backend.app
```

Open `http://127.0.0.1:5000`.

## AI configuration
Copy `.env.example` to `.env` and set `OPENAI_API_KEY` to enable the LLM Analyzer/Copilot. Without it, NEXUS-X remains functional using deterministic local intelligence.

## Demo account
Development mode can seed:

- Email: `demo@nexus-x.local`
- Password: `demo123`

For production, set `NEXUS_ENV=production`, provide a strong 32+ character `NEXUS_SECRET_KEY`, disable demo seeding, and use secure cookies/HTTPS.

## Important verification rule
Do not claim the build is production-ready merely because the package was created. Run the full regression suite and complete the browser/E2E/security checks on the target machine.


## Product database
NEXUS-X supports PostgreSQL as the production database through `DATABASE_URL`, with Alembic migrations. Set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DB` and run `python -m alembic upgrade head`. SQLite remains available as the zero-configuration local fallback. Set `NEXUS_AUTO_MIGRATE=1` to let the application bootstrap PostgreSQL migrations at startup.
