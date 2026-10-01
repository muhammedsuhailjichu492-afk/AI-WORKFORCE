"""
Populates the database with a realistic demo dataset: one IT company's
project portfolio, a small team with varying workloads, and tasks positioned
to trigger every part of the pipeline (overload, blocked tasks, near-term
deadlines, an already-overdue task, etc).

Run:  python -m backend.seed_data
"""
from datetime import date, timedelta
from backend.database import init_db, SessionLocal, Employee, Project, Task


def seed():
    init_db()
    db = SessionLocal()

    # Wipe existing demo data for a clean re-run
    db.query(Task).delete()
    db.query(Project).delete()
    db.query(Employee).delete()
    db.commit()

    today = date.today()

    employees = [
        Employee(name="Aditi Rao", role="Backend Engineer", weekly_capacity_hours=40, skill_tags="api,backend,database"),
        Employee(name="Ben Ortiz", role="Frontend Engineer", weekly_capacity_hours=40, skill_tags="ui,frontend,react"),
        Employee(name="Chen Wei", role="Data Scientist", weekly_capacity_hours=40, skill_tags="ml,data,model"),
        Employee(name="Divya Nair", role="QA Engineer", weekly_capacity_hours=35, skill_tags="testing,qa"),
        Employee(name="Ethan Cole", role="DevOps Engineer", weekly_capacity_hours=40, skill_tags="infra,deploy,devops"),
    ]
    db.add_all(employees)
    db.commit()
    for e in employees:
        db.refresh(e)

    aditi, ben, chen, divya, ethan = employees

    projects = [
        Project(
            name="Client Portal Revamp",
            description="Rebuild the client-facing portal with new auth and dashboard.",
            start_date=today - timedelta(days=20),
            deadline=today + timedelta(days=14),
            status="active",
        ),
        Project(
            name="Internal Analytics Platform",
            description="Self-serve analytics for the ops team.",
            start_date=today - timedelta(days=10),
            deadline=today + timedelta(days=30),
            status="active",
        ),
    ]
    db.add_all(projects)
    db.commit()
    for p in projects:
        db.refresh(p)

    portal, analytics = projects

    tasks = [
        # --- Client Portal Revamp: deliberately overloads Aditi, one overdue task ---
        Task(project_id=portal.id, title="Design new auth API", estimated_hours=16, hours_logged=10,
             priority="critical", status="in_progress", deadline=today + timedelta(days=2),
             assignee_id=aditi.id, is_blocked=False, days_delayed=1),
        Task(project_id=portal.id, title="Implement JWT refresh flow", estimated_hours=12, hours_logged=2,
             priority="high", status="in_progress", deadline=today + timedelta(days=4),
             assignee_id=aditi.id, is_blocked=False, days_delayed=0),
        Task(project_id=portal.id, title="Migrate legacy user table", estimated_hours=20, hours_logged=4,
             priority="high", status="blocked", deadline=today - timedelta(days=1),
             assignee_id=aditi.id, is_blocked=True, days_delayed=6),
        Task(project_id=portal.id, title="Build dashboard widgets", estimated_hours=18, hours_logged=6,
             priority="medium", status="in_progress", deadline=today + timedelta(days=10),
             assignee_id=ben.id, is_blocked=False, days_delayed=0),
        Task(project_id=portal.id, title="Portal visual QA pass", estimated_hours=8, hours_logged=0,
             priority="medium", status="not_started", deadline=today + timedelta(days=12),
             assignee_id=divya.id, is_blocked=False, days_delayed=0),
        Task(project_id=portal.id, title="Set up staging deploy pipeline", estimated_hours=10, hours_logged=8,
             priority="low", status="in_progress", deadline=today + timedelta(days=6),
             assignee_id=ethan.id, is_blocked=False, days_delayed=0),

        # --- Internal Analytics Platform: Chen underused elsewhere, Ben light too ---
        Task(project_id=analytics.id, title="Design churn prediction model", estimated_hours=24, hours_logged=4,
             priority="high", status="in_progress", deadline=today + timedelta(days=20),
             assignee_id=chen.id, is_blocked=False, days_delayed=0),
        Task(project_id=analytics.id, title="Build ETL pipeline", estimated_hours=16, hours_logged=0,
             priority="medium", status="not_started", deadline=today + timedelta(days=18),
             assignee_id=ethan.id, is_blocked=False, days_delayed=0),
        Task(project_id=analytics.id, title="Analytics UI mockups", estimated_hours=6, hours_logged=0,
             priority="low", status="not_started", deadline=today + timedelta(days=25),
             assignee_id=ben.id, is_blocked=False, days_delayed=0),
        Task(project_id=analytics.id, title="Write test suite for ETL", estimated_hours=8, hours_logged=0,
             priority="medium", status="not_started", deadline=today + timedelta(days=22),
             assignee_id=divya.id, is_blocked=False, days_delayed=0),
    ]
    db.add_all(tasks)
    db.commit()
    db.close()

    print("Seed complete:")
    print(f"  {len(employees)} employees, {len(projects)} projects, {len(tasks)} tasks")
    print("  Aditi Rao is intentionally overloaded + has a blocked/overdue task,")
    print("  Chen Wei and Ben Ortiz have spare capacity — good for testing reallocation.")


if __name__ == "__main__":
    seed()
