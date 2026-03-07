from fastapi import FastAPI
from SERVER.routes import habits, leaderboard
from SERVER import storage
from datetime import datetime, date, timedelta

app = FastAPI(
    title="Habit Tracker API",
    version="1.0.0",
    description="API для трекера звичок із підтримкою streak та лідерборду",
)

app.include_router(leaderboard.router)
app.include_router(habits.router)


def seed():
    demo = [
        {"name": "Ранкова пробіжка",    "category": "sport",  "frequency": "daily",  "streak": 12},
        {"name": "Читання 30 хвилин",   "category": "study",  "frequency": "daily",  "streak": 7},
        {"name": "Медитація",           "category": "health", "frequency": "daily",  "streak": 9},
        {"name": "Без цукру",           "category": "health", "frequency": "daily",  "streak": 3},
        {"name": "Тижневий огляд цілей","category": "study",  "frequency": "weekly", "streak": 4},
        {"name": "Вечірня прогулянка",  "category": "sport",  "frequency": "daily",  "streak": 1},
        {"name": "Щоденник",            "category": "health", "frequency": "daily",  "streak": 5},
    ]
    today = date.today()
    for item in demo:
        hid = storage.get_next_id()
        storage.save({
            "id":            hid,
            "name":          item["name"],
            "category":      item["category"],
            "frequency":     item["frequency"],
            "streak":        item["streak"],
            "last_check_in": (today - timedelta(days=1)).isoformat(),
            "created_at":    datetime.now().isoformat(),
        })


seed()