# SentinelAI

SentinelAI is an **agentic AI incident-ticketing application**. Its Day-30 goal is to accept incident reports, autonomously triage and investigate them with evidence tools, maintain a durable investigation record, request human approval before remediation, and update each ticket through resolution.

The agent is designed for bounded autonomy: it may choose approved investigation tools and propose the next action, while the backend remains authoritative for ticket transitions, permissions, budgets, approvals, and side effects.

## Current implementation status

The repository currently implements the **Days 1-2 foundation**:

- Typed FastAPI service with health and database-readiness endpoints.
- Next.js dashboard shell.
- PostgreSQL with pgvector through Docker Compose.
- Python and TypeScript linting, type checks, tests, builds, and GitHub Actions CI.
- A deterministic incident domain model and golden evidence fixture with logs, metrics, and deployment history.

LangGraph orchestration, LLM integration, retrieval, ticket persistence/API, the full ticketing UI, OpenTelemetry, approval execution, and the complete evaluation suite are **planned work**, not current capabilities.

## Day-30 product target

### Ticket lifecycle

```text
New -> Triaged -> Investigating
                         |-> Waiting for information --|
                         |-> Waiting for approval ------|-> Remediating -> Resolved -> Closed
                         |-> Failed
```

A ticket will hold reporter context, comments, investigation runs, normalized evidence, cited hypotheses, information requests, remediation proposals, approvals, and an append-only audit history. Every transition will be validated by backend domain policy.

### Agentic investigation workflow

The core agent will be one typed, bounded LangGraph `StateGraph`:

```text
triage_ticket
  -> plan_investigation
  -> select_tool
  -> collect_evidence
  -> rank_hypotheses
  -> decide_next_step
       |-> request_information
       |-> propose_remediation -> wait_for_approval -> execute_remediation
       |-> resolve_ticket
       |-> safe terminal state
```

This is agentic because the workflow observes ticket state, selects authorized tools, evaluates the collected evidence, and chooses among conditional next steps. It is not an unrestricted autonomous loop: step, tool, and time budgets bound execution; conclusions require citations; insufficient evidence becomes an explicit information request; and remediation requires human approval.

The investigation tools will correlate five evidence categories:

- Logs
- Metrics
- Deployments
- Runbooks retrieved with pgvector
- Dependency and upstream-service signals

### Target architecture

```text
Reporter / Reviewer
        |
        v
Next.js ticket inbox and detail UI
        |
        v
FastAPI ticket service  <---->  PostgreSQL + pgvector
        |                              |
        v                              +-> tickets, evidence, audit history
Bounded LangGraph StateGraph           +-> durable graph checkpoints
        |
        +-> authorized evidence tools
        +-> retrieval and hypothesis ranking
        +-> human approval gate
        +-> OpenTelemetry traces
```

See [docs/architecture.md](docs/architecture.md) for the current service boundaries and design decisions. The architecture above is the planned end state and will be updated as implementation evidence replaces design assumptions.

## Evaluation strategy

The deterministic evaluation suite will cover four portfolio incident classes:

1. Faulty deployment.
2. Database connection exhaustion.
3. Payment-provider timeout.
4. Memory leak.

Each scenario will declare the expected cause and required evidence. Separate safety and uncertainty variants will cover ambiguous evidence, no-fault evidence, injected runbook content, and stale or replayed approvals.

The suite will score the investigation process—not only the final text—including triage, tool selection, evidence recall, root-cause ranking, citation completeness, ticket-state correctness, policy compliance, and bounded termination.

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
venv\Scripts\python -m pip install -e '.[dev]'
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

## Golden incident dataset

The backend packages a fixed-seed checkout-latency incident at `backend/src/sentinel_api/data/golden_incident.json`. Its incident, telemetry, evidence, hypothesis, run, and audit records are validated by Pydantic contracts. Every log, metric, and deployment item includes a typed source and timezone-aware observation timestamp.

Regenerate it from `backend/` with:

```powershell
venv\Scripts\python -m sentinel_api.fixtures
```

## 30-day roadmap

- Days 1-4: service foundation, deterministic evidence, operational ticket domain, persistence, and ticket API.
- Days 5-9: typed evidence tools, runbook retrieval with pgvector, and evidence-citation contracts.
- Days 10-16: bounded LangGraph investigation workflow, model integration, safety policies, and durable checkpoints.
- Days 17-19: OpenTelemetry, auditability, and human approval controls.
- Days 20-22: ticket inbox/detail UI, evidence and hypothesis views, information requests, and end-to-end approval flow.
- Days 23-27: four-class deterministic evaluation, adversarial cases, performance, and reliability.
- Days 28-30: deployment, documentation, demo evidence, and portfolio polish.

The detailed implementation plan and daily learning outcomes are maintained in the project's Notion board.

## Current limitations

- The current dashboard is a foundation shell and does not create tickets or launch investigations.
- `/ready` requires a running PostgreSQL instance; `/health` does not.
- The current golden dataset represents one checkout-latency scenario; the four-class suite is planned.
- No LangGraph agent, LLM provider, runbook retrieval, durable ticket workflow, or remediation path is implemented yet.

## License

MIT
