
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, Employee, Project, Task, Recommendation
from backend import schemas
from backend.agents.orchestrator import run_pipeline
from backend.agents.project_analysis import analyze_projects
from backend.agents.workload_analysis import analyze_workload
from backend.agents.approval import decide_recommendation

app = FastAPI(
    title="AI Project & Workforce Management Agent",
    description="Agentic PM system: monitors tasks/workload, predicts delay risk, "
                "and recommends task reallocation for manager approval.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ---------- Employees ----------

@app.post("/employees", response_model=schemas.EmployeeOut)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    e = Employee(**payload.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@app.get("/employees", response_model=List[schemas.EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()


# ---------- Projects ----------

@app.post("/projects", response_model=schemas.ProjectOut)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    p = Project(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@app.get("/projects", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


# ---------- Tasks ----------

@app.post("/tasks", response_model=schemas.TaskOut)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    t = Task(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@app.get("/tasks", response_model=List[schemas.TaskOut])
def list_tasks(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(Task)
    if project_id:
        q = q.filter(Task.project_id == project_id)
    return q.all()


# ---------- Pipeline stages (individually callable) ----------

@app.get("/analysis/projects")
def get_project_analysis(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    return analyze_projects(db, project_id)


@app.get("/analysis/workload")
def get_workload_analysis(db: Session = Depends(get_db)):
    return analyze_workload(db)


@app.post("/pipeline/run")
def run_full_pipeline(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Runs Project Analysis -> Workload Analysis -> Risk Prediction ->
    Planning Agent -> Recommendation. Recommendations land as 'pending'
    for a human to approve via /recommendations/{id}/decide."""
    return run_pipeline(db, project_id)


# ---------- Recommendations & Approval ----------

@app.get("/recommendations", response_model=List[schemas.RecommendationOut])
def list_recommendations(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Recommendation)
    if status:
        q = q.filter(Recommendation.status == status)
    return q.order_by(Recommendation.created_at.desc()).all()


@app.post("/recommendations/{rec_id}/decide", response_model=schemas.RecommendationOut)
def decide(rec_id: int, payload: schemas.ApprovalDecision, db: Session = Depends(get_db)):
    try:
        return decide_recommendation(db, rec_id, payload.approve, payload.decided_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "date": date.today().isoformat()}


# ---------- Web app (served at http://localhost:8000/) ----------
# Mounted last so it never shadows the API routes above.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
