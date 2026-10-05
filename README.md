# Практическое задание №1 — вариант 12

Прототип серверной части веб-приложения с удалённым вызовом процедур по TCP.
Данные хранятся только в оперативной памяти и на диск не сохраняются.

## Модель данных

Табличные записи представлены **кортежами**.

### Participant

```python
(identifier, datetime, locale, platform)
```

### Assignment

```python
(identifier, datetime, input, participant, tags, stage)
```

Поле `participant` ссылается на `Participant.identifier`.

### Result

```python
(identifier, datetime, response, stage, exception, assignment, cache_hit)
```

Поле `assignment` ссылается на `Assignment.identifier`.

Для каждой сущности реализованы четыре операции:

- создание новой записи;
- получение всех записей;
- получение одной записи по идентификатору;
- редактирование записи.

Специальная выборка возвращает поля `A.input`, `P.platform`, `R.cache_hit`:

```text
π_(A.input, P.platform, R.cache_hit) (
    P ⋈_(P.identifier = A.participant) (
        A ⋈_(A.identifier = R.assignment) (
            σ_(R.datetime >= now - 5 min) (R)
        )
    )
)
```

Всего в модели 13 RPC-операций.

## Структура проекта

```text
src/
  model.py       # модель слоя доступа к данным
  repl.py        # интерактивный режим
  rpc.py         # протокол, сервер, диспетчер и клиент
  server.py      # точка запуска TCP-сервера
tests/
  test_mbt.py    # Model-Based Testing на Hypothesis
  test_model.py  # тест выборки
.gitignore
Makefile
README.md
requirements.txt
run.sh
```

## Установка

Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS / Git Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Этап 1 — модель и REPL

Запуск в Windows CMD:

```cmd
python -m src.repl
```

Запуск в Linux / macOS / Git Bash:

```bash
make repl
```

### Пример работы REPL

```text
variant12> create_participant {"identifier": 1, "datetime": 1000, "locale": "ru_RU", "platform": "windows"}
(1, 1000, 'ru_RU', 'windows')

variant12> create_assignment {"identifier": 10, "datetime": 1000, "input": "task_input", "participant": 1, "tags": "tag1", "stage": "new"}
(10, 1000, 'task_input', 1, 'tag1', 'new')

variant12> create_result {"identifier": 100, "datetime": 1000, "response": "ok", "stage": "done", "exception": "", "assignment": 10, "cache_hit": 1}
(100, 1000, 'ok', 'done', '', 10, 1)

variant12> get_participants
[(1, 1000, 'ru_RU', 'windows')]

variant12> get_participant 1
(1, 1000, 'ru_RU', 'windows')

variant12> recent_input_platform_cache_hit 1100
[('task_input', 'windows', 1)]

variant12> recent_input_platform_cache_hit 2000
[]
```

Пример обработки ошибки:

```text
variant12> get_participant 999
error: Participant with identifier=999 not found
```

## Этап 2 — RPC по TCP

Порядок байт: little-endian. Тело запроса и ответа — в формате JSON.

### Формат запроса

| Поле          | Смещение | Размер     |
|---------------|----------|------------|
| Код операции  | 0        | 1 байт     |
| Размер тела   | 1        | 5 байт     |
| JSON-тело     | 6        | переменный |

### Формат ответа

| Поле                | Смещение | Размер     |
|---------------------|----------|------------|
| Версия протокола    | 0        | 1 байт     |
| Код операции        | 1        | 1 байт     |
| Размер тела ответа  | 2        | 4 байта    |
| JSON-тело           | 6        | переменный |

Версия протокола: 1.

Все запросы и ответы журналируются в файл `journal.log`.

### Запуск сервера

Windows CMD:

```cmd
python -m src.server
```

Linux / macOS / Git Bash:

```bash
./run.sh
```

Сервер слушает 127.0.0.1:9000.

### Пример RPC-клиента

```python
from src.rpc import RPCClient

client = RPCClient()

profile = client.create_participant(
    identifier=1,
    datetime=1000,
    locale="ru_RU",
    platform="windows",
)
print(profile)

print(client.get_participants())
```

### Коды RPC-операций

| Код | Метод                            |
|-----|----------------------------------|
| 1   | create_participant               |
| 2   | get_participants                 |
| 3   | get_participant                  |
| 4   | edit_participant                 |
| 5   | create_assignment                |
| 6   | get_assignments                  |
| 7   | get_assignment                   |
| 8   | edit_assignment                  |
| 9   | create_result                    |
| 10  | get_results                      |
| 11  | get_result                       |
| 12  | edit_result                      |
| 13  | recent_input_platform_cache_hit  |

## Этап 3 — Model-Based Testing

Тестирование RPC реализовано с помощью `RuleBasedStateMachine` из библиотеки `hypothesis`.

Схема:

```text
Hypothesis -> RPCClient -> TCP -> RPCServer -> DataModel
```

Тест параллельно работает с RPC и с локальной моделью и сравнивает их состояние.

### Запуск тестов

Windows CMD:

```cmd
pytest -v
```

Linux / macOS / Git Bash:

```bash
make test
```

### Branch coverage

```bash
coverage run --branch -m pytest
coverage report -m
```

Тесты завершаются без ошибок. Отчёт coverage подтверждает покрытие 13 RPC-методов тестами Hypothesis.

## Git-история

Работа разделена на отдельные коммиты по этапам:

- chore: init project structure
- feat(model): implement variant 12 data model
- feat(repl): add interactive REPL for data model
- feat(rpc): implement TCP RPC server and client
- test(mbt): add Hypothesis model-based tests
- docs: update README and add entry points

## Публикация

Репозиторий публичный. После публикации на GitHub:

1. открыть README.md;
2. сохранить его в PDF через печать браузера;
3. загрузить PDF в CDO;
4. добавить в CDO URL публичного репозитория.