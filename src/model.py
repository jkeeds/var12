"""Модель слоя доступа к данным.

Сущности: Participant, Assignment, Result.
Записи хранятся в памяти в виде кортежей (tuple).

Схема кортежей:
    Participant: (identifier, datetime, locale, platform)
    Assignment:  (identifier, datetime, input, participant,
                  tags, stage)
    Result:      (identifier, datetime, response, stage,
                  exception, assignment, cache_hit)
"""

from typing import Any

RECENT_WINDOW_SECONDS = 300

participants: list[tuple] = []
assignments: list[tuple] = []
results: list[tuple] = []

def _find_index(records: list[tuple],
                identifier: int) -> int | None:
    """Возвращает индекс записи по её identifier, либо None."""
    for i, rec in enumerate(records):
        if rec[0] == identifier:
            return i
    return None

def create_participant(identifier: int, datetime: int,
                       locale: str, platform: str) -> tuple:
    """Создать нового участника."""
    if _find_index(participants, identifier) is not None:
        raise ValueError(
            f"Participant with identifier={identifier} "
            f"already exists"
        )
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
        raise ValueError(
            f"Participant with identifier={identifier} "
            f"not found"
        )
    return participants[idx]

def edit_participant(identifier: int, **kwargs: Any) -> tuple:
    """Редактировать участника.

    kwargs: datetime, locale, platform.
    """
    idx = _find_index(participants, identifier)
    if idx is None:
        raise ValueError(
            f"Participant with identifier={identifier} "
            f"not found"
        )
    old = participants[idx]
    new = (
        old[0],
        kwargs.get("datetime", old[1]),
        kwargs.get("locale", old[2]),
        kwargs.get("platform", old[3]),
    )
    participants[idx] = new
    return new

def create_assignment(identifier: int, datetime: int,
                      input: str, participant: int,
                      tags: str, stage: str) -> tuple:
    """Создать новое задание."""
    if _find_index(assignments, identifier) is not None:
        raise ValueError(
            f"Assignment with identifier={identifier} "
            f"already exists"
        )
    if _find_index(participants, participant) is None:
        raise ValueError(
            f"Participant with identifier={participant} "
            f"not found"
        )
    rec = (identifier, datetime, input, participant,
           tags, stage)
    assignments.append(rec)
    return rec

def get_assignments() -> list[tuple]:
    """Получить все задания."""
    return list(assignments)

def get_assignment(identifier: int) -> tuple:
    """Получить одно задание по identifier."""
    idx = _find_index(assignments, identifier)
    if idx is None:
        raise ValueError(
            f"Assignment with identifier={identifier} "
            f"not found"
        )
    return assignments[idx]

def edit_assignment(identifier: int, **kwargs: Any) -> tuple:
    """Редактировать задание.

    kwargs: datetime, input, participant, tags, stage.
    """
    idx = _find_index(assignments, identifier)
    if idx is None:
        raise ValueError(
            f"Assignment with identifier={identifier} "
            f"not found"
        )
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

def create_result(identifier: int, datetime: int,
                  response: str, stage: str,
                  exception: str, assignment: int,


cache_hit: int) -> tuple:
    """Создать новый результат."""
    if _find_index(results, identifier) is not None:
        raise ValueError(
            f"Result with identifier={identifier} "
            f"already exists"
        )
    if _find_index(assignments, assignment) is None:
        raise ValueError(
            f"Assignment with identifier={assignment} "
            f"not found"
        )
    rec = (identifier, datetime, response, stage,
           exception, assignment, cache_hit)
    results.append(rec)
    return rec

def get_results() -> list[tuple]:
    """Получить все результаты."""
    return list(results)

def get_result(identifier: int) -> tuple:
    """Получить один результат по identifier."""
    idx = _find_index(results, identifier)
    if idx is None:
        raise ValueError(
            f"Result with identifier={identifier} "
            f"not found"
        )
    return results[idx]

def edit_result(identifier: int, **kwargs: Any) -> tuple:
    """Редактировать результат.

    kwargs: datetime, response, stage, exception,
    assignment, cache_hit.
    """
    idx = _find_index(results, identifier)
    if idx is None:
        raise ValueError(
            f"Result with identifier={identifier} "
            f"not found"
        )
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

def recent_input_platform_cache_hit(now: int) -> list[tuple]:
    """Выборка по формуле варианта 12.

    pi(A.input, P.platform, R.cache_hit) (
        P JOIN_(P.identifier = A.participant) (
            A JOIN_(A.identifier = R.assignment) (
                SIGMA_(R.datetime >= now - 5 min) (R)
            )
        )
    )

    Возвращает список кортежей (input, platform, cache_hit).
    """
    threshold = now - RECENT_WINDOW_SECONDS
    filtered = [r for r in results if r[1] >= threshold]

    joined: list[tuple] = []
    for a in assignments:
        for r in filtered:
            if a[0] == r[5]:
                joined.append((a, r))

    final: list[tuple] = []
    for p in participants:
        for a, r in joined:
            if p[0] == a[3]:
                final.append((a[2], p[3], r[6]))
    return final

def reset() -> None:
    """Очистить все таблицы."""
    participants.clear()
    assignments.clear()
    results.clear()
    