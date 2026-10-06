import json
import sys

from . import model as m

MIN_ARGS_EDIT = 2
MAX_SPLIT = 2

COMMANDS = {
    "create_participant": m.create_participant,
    "get_participants": m.get_participants,
    "get_participant": m.get_participant,
    "edit_participant": m.edit_participant,
    "create_assignment": m.create_assignment,
    "get_assignments": m.get_assignments,
    "get_assignment": m.get_assignment,
    "edit_assignment": m.edit_assignment,
    "create_result": m.create_result,
    "get_results": m.get_results,
    "get_result": m.get_result,
    "edit_result": m.edit_result,
    "recent_input_platform_cache_hit": m.recent_input_platform_cache_hit,
    "reset": m.reset,
}

NO_ARGS = (
    "get_participants",
    "get_assignments",
    "get_results",
    "reset",
)

ONE_ID = (
    "get_participant",
    "get_assignment",
    "get_result",
    "recent_input_platform_cache_hit",
)

HELP_TEXT = """Доступные команды:

  Participant:
    create_participant <json>
    get_participants
    get_participant <id>
    edit_participant <id> <json>

  Assignment:
    create_assignment <json>
    get_assignments
    get_assignment <id>
    edit_assignment <id> <json>

  Result:
    create_result <json>
    get_results
    get_result <id>
    edit_result <id> <json>

  Специальные:
    recent_input_platform_cache_hit <now>
    reset
    help
    exit

Формат JSON: {"key": value, ...}
"""


def _parse_json(text: str) -> dict:
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
    try:
        return int(text.strip())
    except ValueError as e:
        raise ValueError(f"expected integer id, got: {text!r}") from e


def _call_no_args(func):
    return func()


def _call_one_id(cmd: str, func, rest: list):
    if len(rest) < 1:
        raise ValueError(f"usage: {cmd} <id>")
    return func(_parse_id(rest[0]))


def _call_create(cmd: str, func, rest: list):
    if len(rest) < 1:
        raise ValueError(f"usage: {cmd} <json>")
    return func(**_parse_json(" ".join(rest)))


def _call_edit(cmd: str, func, rest: list):
    if len(rest) < MIN_ARGS_EDIT:
        raise ValueError(f"usage: {cmd} <id> <json>")
    identifier = _parse_id(rest[0])
    data = _parse_json(rest[1])
    return func(identifier, **data)


def _dispatch(cmd: str, rest: list, func):
    if cmd in NO_ARGS:
        return _call_no_args(func)
    if cmd in ONE_ID:
        return _call_one_id(cmd, func, rest)
    if cmd.startswith("create_"):
        return _call_create(cmd, func, rest)
    if cmd.startswith("edit_"):
        return _call_edit(cmd, func, rest)
    raise ValueError(f"unhandled command '{cmd}'")


def handle(line: str) -> None:
    line = line.strip()
    if not line:
        return

    parts = line.split(maxsplit=MAX_SPLIT)
    cmd = parts[0]
    rest = parts[1:]

    if cmd in ("exit", "quit"):
        print("bye")
        sys.exit(0)

    if cmd in ("help", "?"):
        print(HELP_TEXT)
        return

    if cmd not in COMMANDS:
        msg = f"error: unknown command '{cmd}'. " "Type 'help' for list."
        print(msg)
        return

    try:
        result = _dispatch(cmd, rest, COMMANDS[cmd])
        print(result)
    except TypeError as e:
        print(f"error: wrong arguments for '{cmd}': {e}")
    except ValueError as e:
        print(f"error: {e}")


def main() -> None:
    print("REPL for variant 12 data model. " "Type 'help', 'exit' to quit.")
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
