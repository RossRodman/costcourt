# CostCourt

> **Put your construction estimate on trial.** CostCourt is an AI-powered estimate review tool: three agents argue over every line, a judge rules, and every argument, rebuttal and ruling ends up in an auditable report.

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.x-1C3C3C)
![Claude](https://img.shields.io/badge/LLM-Claude-D97757)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)

## The idea

Checking a construction estimate is adversarial by nature: the person who wrote it defends it, the engineer questions quantities and specs, and the contractor pushes back on anything that squeezes the margin. This project models that process as a multi-agent debate:

| Agent | Role |
|---|---|
| **Estimator** | Wrote the estimate and defends quantities, unit rates and totals. |
| **Engineer** | Checks the technical side: scope gaps, wrong specs, quantities that don't match the design. |
| **Contractor's advocate** | Argues for realistic labour, logistics, risk and margin, and flags rates that are too low to be built for. |
| **Judge** | Reads the whole debate and rules on each disputed line: accepted, adjusted (with a new figure) or rejected, with reasoning. |

The debate runs as a **LangGraph** state machine over a configurable number of rounds. Every agent returns **Pydantic**-validated structured output from **Claude**, so the final report is data first and prose second.

## Tech stack

| | |
|---|---|
| **Backend** | Python 3.11+, FastAPI, LangGraph, Anthropic SDK (Claude), Pydantic v2 |
| **Client** | React 19, TypeScript, Vite, Tailwind CSS v4, lucide icons |
| **Quality** | ruff, mypy (strict), pytest · oxlint, Prettier, Vitest + Testing Library · pre-commit · GitHub Actions |

## Quick start

Requires Python 3.11+ and Node 20.19+.

```bash
# Backend: http://127.0.0.1:8000/api/docs
cd backend
cp .env.example .env              # add your ANTHROPIC_API_KEY
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/costcourt

# Client: http://localhost:5173 (in a second terminal)
cd client
npm ci
npm run dev
```

### Checks (same as CI)

```bash
cd backend && .venv/bin/ruff check . && .venv/bin/mypy && .venv/bin/pytest --cov
cd client && npm run lint && npm run typecheck && npm test
```

## Project layout

```
.
├── backend/                  # FastAPI + LangGraph service
│   ├── app/
│   │   ├── main.py           # app factory
│   │   ├── api/              # HTTP layer: router, routes/, shared deps
│   │   ├── core/             # settings, logging, base model, money types
│   │   ├── estimates/        # estimate model, sample catalog, /api/estimates
│   │   └── debate/           # roles, arguments, rulings, verdict, report
│   └── tests/
├── client/                   # React + Vite single-page app
│   └── src/
│       ├── components/
│       ├── hooks/
│       └── lib/              # typed API client, utils
└── .github/workflows/ci.yml  # backend + client jobs
```

The backend follows FastAPI's official full-stack template (`app/` with `api/` and `core/`). Business logic lives in feature packages (estimates, agents, debate, reports), so routes stay thin. In dev, Vite proxies `/api` to FastAPI, so no CORS setup is needed.

## Domain model

- **Estimate**: scope, location, currency, priced **line items** (quantity × unit rate) and **markups** (overhead, profit, contingency, tax). Totals are computed, never stored, so they can't drift.
- **Turn**: one debater's statement in a round, made of **arguments** about specific line items. Each argument either supports the line, proposes a higher or lower figure, or flags missing scope.
- **Verdict**: the judge's **rulings** per disputed line (accepted / adjusted / rejected), with reasoning and the debaters it sided with.
- **DebateReport**: the original estimate, every turn, the verdict, the revised estimate and the cost impact.

Money is `Decimal`, rounded half-up to cents. Models are immutable and reject unknown fields, and the same models serve as the agents' structured-output contracts.

Three sample estimates (`backend/app/estimates/samples/`) ship with deliberate, realistic problems for the agents to find: stale rates, under-measured reinforcement, missing waste allowances and a zero contingency on a risky site.

## Roadmap

The project is built in small, reviewable pull requests:

- [x] **1. Project setup**: FastAPI backend and React/Vite client skeletons, typed settings, linting, strict typing, tests, CI
- [x] **2. Domain model**: Pydantic models for estimates, line items, arguments, rulings and reports, plus sample estimates
- [ ] **3. Agents**: Claude client wrapper, role prompts and structured outputs for the estimator, engineer, advocate and judge
- [ ] **4. Debate graph**: LangGraph orchestration of rounds and judging, tested with a fake LLM
- [ ] **5. Reports**: decision trail rendered to Markdown, HTML and JSON
- [ ] **6. Web UI**: React screens to upload or pick an estimate, watch the debate stream live (SSE) and read the verdict
- [ ] **7. Polish**: Docker, screenshots, docs

## Configuration

All settings are environment variables (see [`backend/.env.example`](backend/.env.example)). The main ones:

| Variable | Default | |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Needed to run debates |
| `COSTCOURT_DEBATER_MODEL` | `claude-sonnet-5-5` | Model for the three debaters |
| `COSTCOURT_JUDGE_MODEL` | `claude-opus-5-5` | Model for the judge |
| `COSTCOURT_DEBATE_ROUNDS` | `2` | Number of rounds (1–5) |
