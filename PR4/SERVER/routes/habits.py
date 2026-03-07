from fastapi import APIRouter, Query
from typing import Optional

from SERVER.models import Habit, HabitCreate
from SERVER.services import habit_service

router = APIRouter(prefix="/api/habits", tags=["Habits"])


@router.get("", response_model=list[Habit])
def list_habits(category: Optional[str] = Query(default=None)):
    """Список усіх звичок з опціональним фільтром за категорією."""
    return habit_service.get_all_habits(category)


@router.post("", response_model=Habit, status_code=201)
def create_habit(habit: HabitCreate):
    """Створити нову звичку."""
    return habit_service.create_habit(habit)


@router.get("/{habit_id}", response_model=Habit)
def get_habit(habit_id: int):
    """Отримати звичку за ID."""
    return habit_service.get_habit_or_404(habit_id)


@router.put("/{habit_id}", response_model=Habit)
def update_habit(habit_id: int, habit: HabitCreate):
    """Повністю оновити звичку."""
    return habit_service.update_habit(habit_id, habit)


@router.delete("/{habit_id}")
def delete_habit(habit_id: int):
    """Видалити звичку."""
    deleted = habit_service.delete_habit(habit_id)
    return {"message": "Звичку успішно видалено", "habit": deleted}


@router.patch("/{habit_id}/check-in", response_model=Habit)
def check_in(habit_id: int):
    """Відмітити виконання звички (збільшує streak)."""
    return habit_service.check_in(habit_id)
