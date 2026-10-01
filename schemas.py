from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    name: str
    role: str
    weekly_capacity_hours: float = 40.0
    skill_tags: str = ""


class EmployeeOut(EmployeeCreate):
    id: int
    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    start_date: date
    deadline: date
    status: str = "active"


class ProjectOut(ProjectCreate):
    id: int
    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    project_id: int
    title: str
    estimated_hours: float = 8.0
    hours_logged: float = 0.0
    priority: str = "medium"
    status: str = "not_started"
    deadline: date
    assignee_id: Optional[int] = None
    is_blocked: bool = False
    days_delayed: int = 0


class TaskOut(TaskCreate):
    id: int
    class Config:
        from_attributes = True


class RiskOut(BaseModel):
    task_id: int
    task_title: str
    risk_score: float
    risk_level: str
    factors: dict
    explanation: str


class RecommendationOut(BaseModel):
    id: int
    rec_type: str
    task_id: Optional[int]
    from_employee_id: Optional[int]
    to_employee_id: Optional[int]
    description: str
    rationale: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    approve: bool
    decided_by: str = "manager"


class PipelineResult(BaseModel):
    project_analysis: dict
    workload_analysis: dict
    risk_predictions: List[RiskOut]
    plan: dict
    recommendations: List[RecommendationOut]
