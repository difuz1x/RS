

from datetime import date, datetime, timedelta
from fastapi import HTTPException

from SERVER import storage
from SERVER.models import HabitCreate


def create_habit(data: HabitCreate) -> dict:
    habit_id = storage.get_next_id()
    habit = data.model_dump()
    habit["id"] = habit_id
    habit["streak"] = 0
    habit["last_check_in"] = None
    habit["created_at"] = datetime.now().isoformat()
    return storage.save(habit)


def get_all_habits(category: str | None) -> list[dict]:
    result = storage.get_all()
    if category:
        result = [h for h in result if h["category"].lower() == category.lower()]
    return result


def get_habit_or_404(habit_id: int) -> dict:
    habit = storage.get_by_id(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail=f"Звичку з ID {habit_id} не знайдено")
    return habit


def update_habit(habit_id: int, data: HabitCreate) -> dict:
    existing = get_habit_or_404(habit_id)
    updated = data.model_dump()
    updated["id"] = habit_id
    updated["streak"] = existing["streak"]
    updated["last_check_in"] = existing["last_check_in"]
    updated["created_at"] = existing["created_at"]
    return storage.save(updated)


def delete_habit(habit_id: int) -> dict:
    get_habit_or_404(habit_id)
    return storage.delete(habit_id)


def check_in(habit_id: int) -> dict:
    habit = get_habit_or_404(habit_id)
    today = date.today()
    last = habit["last_check_in"]

    if last is not None:
        last_date = date.fromisoformat(last)

        if habit["frequency"] == "daily":
            if last_date == today:
                raise HTTPException(status_code=400, detail="Check-in вже виконано сьогодні!")
            if today - last_date > timedelta(days=1):
                habit["streak"] = 0

        elif habit["frequency"] == "weekly":
            this_week = today.isocalendar()[:2]
            last_week = last_date.isocalendar()[:2]
            if this_week == last_week:
                raise HTTPException(status_code=400, detail="Check-in вже виконано цього тижня!")
            if today.isocalendar()[1] - last_date.isocalendar()[1] > 1:
                habit["streak"] = 0

    habit["streak"] += 1
    habit["last_check_in"] = today.isoformat()
    return storage.save(habit)


def get_leaderboard(limit: int) -> list[dict]:
    sorted_habits = sorted(storage.get_all(), key=lambda h: h["streak"], reverse=True)
    return sorted_habits[:limit]