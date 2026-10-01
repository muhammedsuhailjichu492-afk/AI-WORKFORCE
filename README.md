# AI Project & Workforce Management Agent

An agentic project manager that monitors tasks, employee workload, deadlines,
and project risk — then recommends task reallocation, deadline extensions,
and priority changes for a human manager to approve.

Implements the pipeline exactly as designed:

```
Project Analysis → Workload Analysis → Risk Prediction → Planning Agent → Recommendation → Approval
```

| Layer | Where it's used |
|---|---|
| **SQL** | `backend/database.py` — SQLAlchemy + SQLite, full schema (employees, projects, tasks, risk predictions, recommendations) |
| **ML** | `backend/agents/ml_risk_model.py` — RandomForest regressor predicting a 0–100 delay-risk score per task |
| **LLM** | `backend/llm_client.py` — local Ollama call to turn structured risk factors into plain-English explanations and recommendation text (RAG-lite: the "context" is the real, retrieved factor data, not a hallucination) |
| **Agents** | `backend/agents/` — one module per pipeline stage, chained by `orchestrator.py` |
| **Optimization** | `backend/agents/planning_agent.py` — constrained greedy reallocation that moves work from overloaded to underutilized employees within capacity limits |

## Project structure

```
ai_workforce_agent/
├── requirements.txt
├── workforce.db                # created on first run (SQLite)
├── backend/
│   ├── main.py                 # FastAPI app — all HTTP endpoints
│   ├── database.py             # Legacy module retained for compatibility
│   ├── database/
│   │   ├── __init__.py         # Workforce database exports
│   │   ├── workforce.py        # SQLAlchemy models + session
│   │   └── db_setup.py         # Enterprise SQLite setup utilities
│   ├── schemas.py               # Pydantic request/response models
│   ├── llm_client.py           # Ollama wrapper (LLM stage)
│   ├── seed_data.py            # demo data generator
│   └── agents/
│       ├── project_analysis.py     # Stage 1
│       ├── workload_analysis.py    # Stage 2
│       ├── ml_risk_model.py        # trained model used by Stage 3
│       ├── risk_prediction.py      # Stage 3
│       ├── planning_agent.py       # Stage 4 (prioritization + optimizer)
│       ├── recommendation.py       # Stage 5
│       ├── approval.py             # Stage 6
│       └── orchestrator.py         # chains stages 1–5
└── frontend/
  ├── index.html               # Browser web interface
  └── dashboard.py             # Optional legacy Streamlit dashboard
```

## Setup (Windows / VS Code / PowerShell)

```powershell
# from the project root, in a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### (Optional) LLM explanations via Ollama

The LLM stage calls a local Ollama server. If it's not running, every
explanation/recommendation falls back to a clean template automatically —
nothing breaks.

```powershell
ollama pull llama3.2:3b     # or edit OLLAMA_MODEL in backend/llm_client.py
ollama serve
```

## Run it

**1. Seed demo data** (5 employees, 2 projects, 10 tasks — deliberately includes
an overloaded employee, a blocked task, and an overdue task so every pipeline
stage has something to react to):

```powershell
python -m backend.seed_data
```

**2. Start the backend:**

```powershell
uvicorn backend.main:app --reload --port 8000
```

API docs (interactive): http://localhost:8000/docs

**3. Open the web interface:**

Open http://127.0.0.1:8000/ in your browser. FastAPI serves the web interface
from `frontend/index.html`; no separate frontend server is required.

**4. Use the approval workflow:**

Click **Run pipeline** to generate recommendations. Review each pending
recommendation, then choose **Accept** or **Reject**. The system never applies a
recommendation automatically: only the manager's decision changes the task.

The optional legacy Streamlit dashboard can still be started with
`streamlit run frontend/dashboard.py`, but it is not required for the web UI.

## Key API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/employees`, `/projects`, `/tasks` | create data |
| GET | `/analysis/projects` | Stage 1 output |
| GET | `/analysis/workload` | Stage 2 output |
| POST | `/pipeline/run` | runs Stages 1–5, stores pending recommendations |
| GET | `/recommendations?status=pending` | list recommendations |
| POST | `/recommendations/{id}/decide` | Stage 6 — approve/reject; approving **applies the effect** (reassigns the task, extends the deadline, or bumps priority) |

## Enterprise intelligence pipeline

The same FastAPI app also exposes the broader enterprise workflow:

```
Supervisor -> Data / SQL / ML / RAG -> Decision -> Risk -> Human Approval -> Action
```

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/enterprise/run` | Run an enterprise analysis for `inventory`, `production`, `sales`, `finance`, `hr`, `quality`, `operations`, or `procurement` |
| GET | `/api/enterprise/approvals` | List approval-gated recommendations |
| POST | `/api/enterprise/approvals/{id}/decide` | Approve or reject a queued action |
| GET | `/api/enterprise/actions` | View executed action history |

ChromaDB is used for persistent policy retrieval when installed. If it is not
available, retrieval falls back to deterministic local embeddings. Ollama is
also optional; SQL generation and decision narratives fall back to safe,
rule-based behavior when the local model is offline.

## Notes on the ML model

`ml_risk_model.py` trains a `RandomForestRegressor` on synthetic-but-realistic
data at process start (~1 second), since a fresh deployment has no historical
delay outcomes to learn from yet. The generator encodes the same risk drivers
a PM would reason about by hand — tight deadline, work remaining, blocked
status, priority, assignee overload, existing delay — with noise added so the
model has to learn the relationship rather than memorize a formula. Swap in
`load_real_training_data()` once you're logging actual task outcomes
(closed-on-time vs. closed-late) for a model trained on your own history.

## Extending it

- **Real skill-based routing**: `planning_agent._skill_match` is currently
  permissive; give tasks structured skill-tag fields to tighten it.
- **True ILP optimizer**: swap the greedy reallocation for
  `scipy.optimize.milp` if you need a provably optimal assignment across many
  employees/tasks at once.
- **RAG over project docs**: the LLM stage is RAG-*lite* (grounded in
  structured factors, not embeddings). Point it at a ChromaDB store of past
  postmortems/specs for richer, cited explanations — the same pattern used in
  this project's other Ollama+ChromaDB work.
