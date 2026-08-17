# SentinelAI

SentinelAI is an agentic incident investigation and response platform. It will investigate simulated production incidents using logs, metrics, deployment history, and runbooks, then produce evidence-backed hypotheses and request human approval before remediation.

This repository currently contains the **Day 1 foundation**: a typed FastAPI service, Next.js dashboard shell, PostgreSQL with pgvector, Docker Compose, automated tests, linting, type checking, and CI.

## Architecture

```text
Browser (Next.js) ---> FastAPI ---> PostgreSQL + pgvector
                           |
                           +----> Agent workflow and tools (Days 2-8)
                           +----> OpenTelemetry (Day 10)
```

See [docs/architecture.md](docs/architecture.md) for boundaries and design decisions.

## Quick start with Docker

Requirements: Docker Desktop with Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

On PowerShell, use `Copy-Item .env.example .env` instead of `cp`.

- Dashboard: http://localhost:3000
- API documentation: http://localhost:8000/docs
- Liveness: http://localhost:8000/health
- Database readiness: http://localhost:8000/ready

Stop services with `docker compose down`. The PostgreSQL data volume is retained.

## Local development

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\python -m pip install -e ".[dev]"
venv\Scripts\python -m uvicorn sentinel_api.main:app --reload
```

Run quality checks:

```powershell
venv\Scripts\python -m ruff check .
venv\Scripts\python -m mypy src
venv\Scripts\python -m pytest
```

### Frontend

PowerShell may block `npm.ps1`; `npm.cmd` works without changing the execution policy.

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Run quality checks:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

## Configuration

Configuration is read from environment variables. Copy `.env.example` for local defaults. Never commit a populated `.env` file or API keys.

## Roadmap

- Day 2: incident domain model and deterministic demo dataset
- Days 3-5: typed diagnostic tools and evidence-driven agent workflow
- Days 6-8: runbook retrieval, durable state, and human approval
- Days 9-10: investigation dashboard and observability
- Days 11-12: evaluations and adversarial security tests
- Days 13-14: deployment, documentation, and portfolio polish

## Current limitations

- The dashboard is a foundation shell and does not yet launch investigations.
- `/ready` requires a running PostgreSQL instance; `/health` does not.
- Agent orchestration, LLM providers, retrieval, and incident data intentionally begin on later days.

## License

MIT
