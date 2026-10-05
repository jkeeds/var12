"""Модель слоя доступа к данным

Сущности: Participant, Assignment, Result.
Записи хранятся в памяти в виде кортежей (tuple).

Схема кортежей:
    Participant: (identifier, datetime, locale, platform)
    Assignment:  (identifier, datetime, input, participant, tags, stage)
    Result:      (identifier, datetime, response, stage, exception, assignment, cache_hit)
"""

from typing import Any

# Хранилища (in-memory)
participants: list[tuple] = []
assignments: list[tuple] = []
results: list[tuple] = []


def _find_index(records: list[tuple], identifier: int) -> int | None:
    """Возвращает индекс записи по её identifier (поле 0), либо None."""
    for i, rec in enumerate(records):
        if rec[0] == identifier:
            return i
    return None


# --- Participant ---

def create_participant(identifier: int, datetime: int, locale: str, platform: str) -> tuple:
    """Создать нового участника."""
    if _find_index(participants, identifier) is not None:
        raise ValueError(f"Participant with identifier={identifier} already exists")
    rec = (identifier, datetime, locale, platform)
    participants.append(rec)
    return rec


def get_participants() -> list[tuple]:
    """Получить всех участников."""
    return list(participants)


def get_participant(identifier: int) -> tuple:
    """Получить одного участника по identifier."""
    idx = _find_index(participants, identifier)
    if idx is None:
        raise ValueError(f"Participant with identifier={identifier} not found")
    return participants[idx]


def edit_participant(identifier: int, **kwargs: Any) -> tuple:
    """Редактировать участника. kwargs: datetime, locale, platform."""
    idx = _find_index(participants, identifier)
    if idx is None:
        raise ValueError(f"Participant with identifier={identifier} not found")
    old = participants[idx]
    new = (
        old[0],
        kwargs.get("datetime", old[1]),
        kwargs.get("locale", old[2]),
        kwargs.get("platform", old[3]),
    )
    participants[idx] = new
    return new


# --- Assignment ---

def create_assignment(
    identifier: int,
    datetime: int,
    input: str,
    participant: int,
    tags: str,
    stage: str,
) -> tuple:
    """Создать новое задание."""
    if _find_index(assignments, identifier) is not None:
        raise ValueError(f"Assignment with identifier={identifier} already exists")
    if _find_index(participants, participant) is None:
        raise ValueError(f"Participant with identifier={participant} not found")
    rec = (identifier, datetime, input, participant, tags, stage)
    assignments.append(rec)
    return rec


def get_assignments() -> list[tuple]:
    """Получить все задания."""
    return list(assignments)


def get_assignment(identifier: int) -> tuple:
    """Получить одно задание по identifier."""
    idx = _find_index(assignments, identifier)
    if idx is None:
        raise ValueError(f"Assignment with identifier={identifier} not found")
    return assignments[idx]


def edit_assignment(identifier: int, **kwargs: Any) -> tuple:
    """Редактировать задание. kwargs: datetime, input, participant, tags, stage."""
    idx = _find_index(assignments, identifier)
    if idx is None:
        raise ValueError(f"Assignment with identifier={identifier} not found")
    old = assignments[idx]
    new = (
        old[0],
        kwargs.get("datetime", old[1]),
        kwargs.get("input", old[2]),
        kwargs.get("participant", old[3]),
        kwargs.get("tags", old[4]),
        kwargs.get("stage", old[5]),
    )
    assignments[idx] = new
    return new


# --- Result ---

def create_result(
    identifier: int,
    datetime: int,
    response: str,
    stage: str,
    exception: str,
    assignment: int,
    cache_hit: int,
) -> tuple:
    """Создать новый результат."""
    if _find_index(results, identifier) is not None:
        raise ValueError(f"Result with identifier={identifier} already exists")
    if _find_index(assignments, assignment) is None:
        raise ValueError(f"Assignment with identifier={assignment} not found")
    rec = (identifier, datetime, response, stage, exception, assignment, cache_hit)
    results.append(rec)
    return rec


def get_results() -> list[tuple]:
    """Получить все результаты."""
    return list(results)


def get_result(identifier: int) -> tuple:
    """Получить один результат по identifier."""
    idx = _find_index(results, identifier)
    if idx is None:
        raise ValueError(f"Result with identifier={identifier} not found")
    return results[idx]


def edit_result(identifier: int, **kwargs: Any) -> tuple:
    """Редактировать результат. kwargs: datetime, response, stage, exception, assignment, cache_hit."""
    idx = _find_index(results, identifier)
    if idx is None:
        raise ValueError(f"Result with identifier={identifier} not found")
    old = results[idx]
    new = (
        old[0],
        kwargs.get("datetime", old[1]),
        kwargs.get("response", old[2]),
        kwargs.get("stage", old[3]),
        kwargs.get("exception", old[4]),
        kwargs.get("assignment", old[5]),
        kwargs.get("cache_hit", old[6]),
    )
    results[idx] = new
    return new


# --- Специальная выборка (13-я функция) ---

def recent_input_platform_cache_hit(now: int) -> list[tuple]:
    """Формула (вариант 12):

        π_(A.input, P.platform, R.cache_hit) (
            P ⋈_(P.identifier = A.participant) (
                A ⋈_(A.identifier = R.assignment) (
                    σ_(R.datetime >= now - 5 min) (R)
                )
            )
        )

    Возвращает список кортежей (input, platform, cache_hit).
    """
    time_threshold = now - 300  # 5 минут = 300 секунд

    # 1) σ: фильтрация Result по времени
    filtered_results = [r for r in results if r[1] >= time_threshold]

    # 2) A ⋈ R по A.identifier = R.assignment
    joined_ar: list[tuple] = []
    for a in assignments:
        for r in filtered_results:
            if a[0] == r[5]:
                joined_ar.append((a, r))

    # 3) P ⋈ (A ⋈ R) + проекция
    final: list[tuple] = []
    for p in participants:
        for a, r in joined_ar:
            if p[0] == a[3]:
                final.append((a[2], p[3], r[6]))
    return final


# --- Сброс ---

def reset() -> None:
    """Очистить все таблицы."""
    participants.clear()
    assignments.clear()
    results.clear()