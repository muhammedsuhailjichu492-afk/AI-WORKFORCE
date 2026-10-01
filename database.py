
from datetime import datetime, date
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, DateTime,
    ForeignKey, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///./workforce.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    weekly_capacity_hours = Column(Float, default=40.0)
    skill_tags = Column(String, default="")  # comma separated, used for RAG-lite matching

    tasks = relationship("Task", back_populates="assignee")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    start_date = Column(Date, default=date.today)
    deadline = Column(Date, nullable=False)
    status = Column(String, default="active")  # active, completed, on_hold

    tasks = relationship("Task", back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    estimated_hours = Column(Float, default=8.0)
    hours_logged = Column(Float, default=0.0)
    priority = Column(String, default="medium")  # low, medium, high, critical
    status = Column(String, default="not_started")  # not_started, in_progress, blocked, done
    deadline = Column(Date, nullable=False)
    assignee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    is_blocked = Column(Boolean, default=False)
    days_delayed = Column(Integer, default=0)  # historical/current delay, drives risk

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Employee", back_populates="tasks")


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    risk_score = Column(Float)          # 0-100, from ML model
    risk_level = Column(String)          # Low / Medium / High / Critical
    factors = Column(Text)               # JSON string of contributing factors
    explanation = Column(Text, default="")  # LLM-generated natural language explanation
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    rec_type = Column(String)            # reassignment, deadline_extension, priority_change, hire_more
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    from_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    to_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    description = Column(Text)
    rationale = Column(Text, default="")  # LLM-generated rationale
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
