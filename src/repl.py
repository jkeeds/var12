"""REPL для модели слоя доступа к данным

Формат команд:
    <имя_функции> [JSON-аргументы]

Примеры:
    create_participant {"identifier": 1, "datetime": 1000, "locale": "ru_RU", "platform": "windows"}
    get_participants
    get_participant 1
    edit_participant 1 {"locale": "en_US"}
    recent_input_platform_cache_hit 1100
    help
    exit
"""

import json
import sys

from . import model as m


COMMANDS = {
    # Participant
    "create_participant": m.create_participant,
    "get_participants": m.get_participants,
    "get_participant": m.get_participant,
    "edit_participant": m.edit_participant,
    # Assignment
    "create_assignment": m.create_assignment,
    "get_assignments": m.get_assignments,
    "get_assignment": m.get_assignment,
    "edit_assignment": m.edit_assignment,
    # Result
    "create_result": m.create_result,
    "get_results": m.get_results,
    "get_result": m.get_result,
    "edit_result": m.edit_result,
    # Специальная выборка
    "recent_input_platform_cache_hit": m.recent_input_platform_cache_hit,
    # Служебные
    "reset": m.reset,
}


HELP_TEXT = """Доступные команды:

  --- Participant ---
  create_participant <json>         создать участника
  get_participants                  получить всех участников
  get_participant <id>              получить участника по id
  edit_participant <id> <json>      редактировать участника

  --- Assignment ---
  create_assignment <json>          создать задание
  get_assignments                   получить все задания
  get_assignment <id>               получить задание по id
  edit_assignment <id> <json>       редактировать задание

  --- Result ---
  create_result <json>              создать результат
  get_results                       получить все результаты
  get_result <id>                   получить результат по id
  edit_result <id> <json>           редактировать результат

  --- Специальные ---
  recent_input_platform_cache_hit <now>
                                    выборка по формуле (input, platform, cache_hit)
  reset                             очистить все таблицы
  help                              показать эту справку
  exit                              выйти

Формат JSON: {"key": value, ...} (одинарные кавычки не поддерживаются)
"""


def _parse_json(text: str) -> dict:
    """Парсит JSON-строку, возвращает dict."""
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("JSON must be an object: {...}")
    return data


def _parse_id(text: str) -> int:
    """Парсит целочисленный идентификатор."""
    try:
        return int(text.strip())
    except ValueError as e:
        raise ValueError(f"expected integer id, got: {text!r}") from e


def handle(line: str) -> None:
    """Обрабатывает одну строку ввода."""
    line = line.strip()
    if not line:
        return

    parts = line.split(maxsplit=2)
    cmd = parts[0]
    rest = parts[1:]

    if cmd in ("exit", "quit"):
        print("bye")
        sys.exit(0)

    if cmd in ("help", "?"):
        print(HELP_TEXT)
        return

    if cmd not in COMMANDS:
        print(f"error: unknown command '{cmd}'. Type 'help' for list.")
        return

    func = COMMANDS[cmd]

    try:
        # --- Команды без аргументов ---
        if cmd in ("get_participants", "get_assignments", "get_results", "reset"):
            result = func()
            print(result)

        # --- Команды с одним id: get_<entity> <id> ---
        elif cmd in ("get_participant", "get_assignment", "get_result"):
            if len(rest) < 1:
                raise ValueError(f"usage: {cmd} <id>")
            identifier = _parse_id(rest[0])
            result = func(identifier)
            print(result)

        # --- recent_input_platform_cache_hit <now> ---
        elif cmd == "recent_input_platform_cache_hit":
            if len(rest) < 1:
                raise ValueError(f"usage: {cmd} <now>")
            now = _parse_id(rest[0])
            result = func(now)
            print(result)

        # --- create_<entity> <json> ---
        elif cmd.startswith("create_"):
            if len(rest) < 1:
                raise ValueError(f"usage: {cmd} <json>")
            data = _parse_json(" ".join(rest))
            result = func(**data)
            print(result)

        # --- edit_<entity> <id> <json> ---
        elif cmd.startswith("edit_"):
            if len(rest) < 2:
                raise ValueError(f"usage: {cmd} <id> <json>")
            identifier = _parse_id(rest[0])
            data = _parse_json(rest[1])
            result = func(identifier, **data)
            print(result)

        else:
            print(f"error: unhandled command '{cmd}'")

    except TypeError as e:
        print(f"error: wrong arguments for '{cmd}': {e}")
    except ValueError as e:
        print(f"error: {e}")


def main() -> None:
    print("REPL for variant 12 data model. Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("variant12> ")
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break
        try:
            handle(line)
        except SystemExit:
            break
        except Exception as e:
            print(f"unexpected error: {e}")


if __name__ == "__main__":
    main()