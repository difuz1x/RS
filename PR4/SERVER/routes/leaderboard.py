from fastapi import APIRouter, Query

from SERVER.models import Habit
from SERVER.services import habit_service

router = APIRouter(prefix="/api/habits", tags=["Leaderboard"])


@router.get("/leaderboard", response_model=list[Habit])
def get_leaderboard(limit: int = Query(default=10, ge=1, le=100)):
    """Топ звичок за streak (від найбільшого до найменшого)."""
    return habit_service.get_leaderboard(limit)