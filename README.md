\# Практическое задание №1 — вариант 12



!\[Python](https://img.shields.io/badge/python-3.13-blue)

!\[Tests](https://img.shields.io/badge/tests-passing-brightgreen)

!\[Coverage](https://img.shields.io/badge/coverage-92%25-green)



Прототип серверной части веб-приложения с удалённым вызовом процедур (RPC) по TCP.

Данные хранятся только в оперативной памяти и на диск не сохраняются.



\## Содержание



\- \[Архитектура](#архитектура)

\- \[Модель данных](#модель-данных)

\- \[Структура проекта](#структура-проекта)

\- \[Установка](#установка)

\- \[Этап 1 — модель и REPL](#этап-1--модель-и-repl)

\- \[Этап 2 — RPC по TCP](#этап-2--rpc-по-tcp)

\- \[Этап 3 — Model-Based Testing](#этап-3--model-based-testing)

\- \[Git-история](#git-история)

\- \[Публикация](#публикация)



\## Архитектура



Проект состоит из трёх слоёв:



1\. \*\*Слой данных\*\* (`src/model.py`) — in-memory хранилище для трёх сущностей:

&#x20;  `Participant`, `Assignment`, `Result`. Операции create / read / edit

&#x20;  плюс специальный запрос `recent\_input\_platform\_cache\_hit`.



2\. \*\*REPL\*\* (`src/repl.py`) — обёртка над моделью, которая парсит

&#x20;  JSON-аргументы и возвращает читаемые результаты. Используется

&#x20;  локально и как backend RPC-сервера.



3\. \*\*RPC-транспорт\*\* (`src/rpc.py`) — бинарный протокол поверх TCP:

&#x20;  1 байт opcode + 5 байт длины + тело JSON. Клиент шлёт opcode +

&#x20;  сериализованные аргументы, сервер диспетчеризует их по таблице

&#x20;  `OPERATIONS`, выполняет метод и возвращает результат.



\## Модель данных



Табличные записи представлены \*\*кортежами\*\* (tuple).



\### Participant



```python

(identifier, datetime, locale, platform)

```



\### Assignment



```python

(identifier, datetime, input, participant, tags, stage)

```



Поле `participant` ссылается на `Participant.identifier`.



\### Result



```python

(identifier, datetime, response, stage, exception, assignment, cache\_hit)

```



Поле `assignment` ссылается на `Assignment.identifier`.



Для каждой сущности реализованы четыре операции:



1\. создание новой записи;

2\. получение всех записей;

3\. получение одной записи по идентификатору;

4\. редактирование записи.



\### Специальная выборка



Формула (реляционная алгебра):



```text

π\_(A.input, P.platform, R.cache\_hit) (

&#x20;   P ⋈\_(P.identifier = A.participant) (

&#x20;       A ⋈\_(A.identifier = R.assignment) (

&#x20;           σ\_(R.datetime >= now - 5 min) (R)

&#x20;       )

&#x20;   )

)

```



Всего в модели \*\*13 операций\*\* (12 CRUD + 1 выборка).



\## Структура проекта



```text

src/

&#x20; \_\_init\_\_.py

&#x20; model.py       # модель слоя доступа к данным

&#x20; repl.py        # интерактивный режим

&#x20; rpc.py         # протокол, сервер, диспетчер и клиент

&#x20; server.py      # точка запуска TCP-сервера

tests/

&#x20; \_\_init\_\_.py

&#x20; test\_model.py  # тест выборки

&#x20; test\_mbt.py    # Model-Based Testing на Hypothesis

.gitignore

Makefile

README.md

requirements.txt

run.sh

```



\## Установка



Windows CMD:



```cmd

python -m venv .venv

.venv\\Scripts\\activate

pip install -r requirements.txt

```



Linux / macOS / Git Bash:



```bash

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

```



\## Этап 1 — модель и REPL



Запуск в Windows CMD:



```cmd

python -m src.repl

```



Запуск в Linux / macOS / Git Bash:



```bash

make repl

```



\### Пример работы REPL



```text

variant12> create\_participant {"identifier": 1, "datetime": 1000, "locale": "ru\_RU", "platform": "windows"}

(1, 1000, 'ru\_RU', 'windows')



variant12> create\_assignment {"identifier": 10, "datetime": 1000, "input": "task\_input", "participant": 1, "tags": "tag1", "stage": "new"}

(10, 1000, 'task\_input', 1, 'tag1', 'new')



variant12> create\_result {"identifier": 100, "datetime": 1000, "response": "ok", "stage": "done", "exception": "", "assignment": 10, "cache\_hit": 1}

(100, 1000, 'ok', 'done', '', 10, 1)



variant12> get\_participants

\[(1, 1000, 'ru\_RU', 'windows')]



variant12> get\_participant 1

(1, 1000, 'ru\_RU', 'windows')



variant12> edit\_participant 1 {"locale": "en\_US"}

(1, 1000, 'en\_US', 'windows')



variant12> recent\_input\_platform\_cache\_hit 1100

\[('task\_input', 'windows', 1)]



variant12> recent\_input\_platform\_cache\_hit 2000

\[]

```



Пример обработки ошибки:



```text

variant12> get\_participant 999

error: Participant with identifier=999 not found

```



\## Этап 2 — RPC по TCP



Порядок байт: \*\*little-endian\*\* (от младшего к старшему).

Тело запроса и ответа — в формате JSON.



\### Формат запроса



| Поле          | Смещение | Размер     |

|---------------|----------|------------|

| Код операции  | 0        | 1 байт     |

| Размер тела   | 1        | 5 байт     |

| JSON-тело     | 6        | переменный |



\### Формат ответа



| Поле                | Смещение | Размер     |

|---------------------|----------|------------|

| Версия протокола    | 0        | 1 байт     |

| Код операции        | 1        | 1 байт     |

| Размер тела ответа  | 2        | 4 байта    |

| JSON-тело           | 6        | переменный |



Версия протокола: `1`.



Все запросы и ответы журналируются в файл `journal.log`.



\### Запуск сервера



Windows CMD:



```cmd

python -m src.server

```



Linux / macOS / Git Bash:



```bash

./run.sh

```



или



```bash

make server

```



Сервер слушает `127.0.0.1:9000`.



\### Пример RPC-клиента



```python

from src.rpc import RPCClient



client = RPCClient()



\# создаём участника

profile = client.create\_participant(

&#x20;   identifier=1,

&#x20;   datetime=1000,

&#x20;   locale="ru\_RU",

&#x20;   platform="windows",

)

print(profile)



\# читаем всех

print(client.get\_participants())



\# специальная выборка

print(client.recent\_input\_platform\_cache\_hit(now=1100))

```



\### Коды RPC-операций



| Код | Метод                            |

|-----|----------------------------------|

| 1   | create\_participant               |

| 2   | get\_participants                 |

| 3   | get\_participant                  |

| 4   | edit\_participant                 |

| 5   | create\_assignment                |

| 6   | get\_assignments                  |

| 7   | get\_assignment                   |

| 8   | edit\_assignment                  |

| 9   | create\_result                    |

| 10  | get\_results                      |

| 11  | get\_result                       |

| 12  | edit\_result                      |

| 13  | recent\_input\_platform\_cache\_hit  |



\## Этап 3 — Model-Based Testing



Тестирование RPC реализовано с помощью `RuleBasedStateMachine` из библиотеки

`hypothesis`. Тест параллельно работает с RPC (по TCP) и с локальной моделью,

после каждого шага сравнивая их состояние.



Схема:



```text

Hypothesis -> RPCClient -> TCP -> RPCServer -> DataModel

```



\### Запуск тестов



Windows CMD:



```cmd

pytest -v

```



Linux / macOS / Git Bash:



```bash

make test

```



\### Branch coverage



```bash

coverage run --branch -m pytest

coverage report -m

```



Текущее покрытие модуля `src/rpc.py` — \*\*92%\*\*. Отчёт coverage подтверждает

покрытие всех 13 RPC-методов тестами Hypothesis.



\## Git-история



Работа разделена на отдельные коммиты по этапам:



\- `chore: init project structure`

\- `feat(model): implement variant 12 data model`

\- `feat(repl): add interactive REPL for data model`

\- `feat(rpc): implement TCP RPC server and client`

\- `test(mbt): add Hypothesis model-based tests`

\- `docs: update README and add entry points`



\## Публикация



Репозиторий публичный. После публикации на GitHub:



1\. открыть `README.md`;

2\. сохранить его в PDF через печать браузера;

3\. загрузить PDF в CDO;

4\. добавить в CDO URL публичного репозитория.

