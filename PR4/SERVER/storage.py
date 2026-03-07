

habits: dict[int, dict] = {}
_next_id: int = 1


def get_next_id() -> int:
    global _next_id
    current = _next_id
    _next_id += 1
    return current


def get_all() -> list[dict]:
    return list(habits.values())


def get_by_id(habit_id: int) -> dict | None:
    return habits.get(habit_id)


def save(habit: dict) -> dict:
    habits[habit["id"]] = habit
    return habit


def delete(habit_id: int) -> dict:
    return habits.pop(habit_id)


def exists(habit_id: int) -> bool:
    return habit_id in habits