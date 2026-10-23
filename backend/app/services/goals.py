"""Savings goals: target amount + date, progress measured against a savings account balance."""
from datetime import date

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import SavingsGoal


class GoalProgress(BaseModel):
    id: int
    name: str
    target: float
    target_date: date
    saved: float
    pct: float
    remaining: float
    months_left: int
    needed_per_month: float
    on_track_note: str


def progress(goal: SavingsGoal, saved: float, monthly_net: float | None = None) -> GoalProgress:
    remaining = max(goal.target - saved, 0.0)
    today = date.today()
    months_left = max((goal.target_date.year - today.year) * 12 + goal.target_date.month - today.month, 1)
    needed = round(remaining / months_left, 2)
    if remaining == 0:
        note = "Goal reached! 🎉"
    elif monthly_net is None:
        note = f"Save ${needed:,.2f}/month to hit it."
    elif monthly_net >= needed:
        note = f"On track — you're netting about ${monthly_net:,.0f}/month."
    else:
        note = f"Behind — you need ${needed:,.0f}/month but are netting about ${monthly_net:,.0f}."
    return GoalProgress(id=goal.id, name=goal.name, target=goal.target, target_date=goal.target_date, saved=round(saved, 2),
                        pct=round(min(saved / goal.target * 100, 100), 1) if goal.target else 0,
                        remaining=round(remaining, 2), months_left=months_left, needed_per_month=needed,
                        on_track_note=note)


def list_goals(db: Session, user_id: str) -> list[SavingsGoal]:
    return db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id).order_by(SavingsGoal.target_date).all()


def add_goal(db: Session, user_id: str, name: str, target: float, target_date: date) -> SavingsGoal:
    name = name.strip()[:60]
    if not name or target <= 0 or target > 10_000_000:
        raise ValueError("Give the goal a name and a positive target.")
    goal = SavingsGoal(user_id=user_id, name=name, target=target, target_date=target_date)
    db.add(goal)
    db.commit()
    return goal


def delete_goal(db: Session, user_id: str, goal_id: int) -> None:
    db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id, SavingsGoal.id == goal_id).delete()
    db.commit()
