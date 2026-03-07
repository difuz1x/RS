from pydantic import BaseModel, field_validator
from typing import Optional


class HabitCreate(BaseModel):
    name: str
    category: Optional[str] = "general"
    frequency: str  # daily" або "weekly

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v not in ("daily", "weekly"):
            raise ValueError("frequency має бути 'daily' або 'weekly'")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("name не може бути порожнім")
        return v.strip()


class Habit(HabitCreate):
    id: int
    streak: int
    last_check_in: Optional[str] = None
    created_at: str