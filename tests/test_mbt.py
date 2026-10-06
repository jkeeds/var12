import socket
import threading
import time

from hypothesis import settings, HealthCheck
from hypothesis.stateful import (
    RuleBasedStateMachine,
    rule,
    precondition,
    run_state_machine_as_test,
)
from hypothesis import strategies as st

from src import model as local
from src.rpc import RPCClient, serve_forever, HOST, PORT

SERVER_STARTUP_TIMEOUT = 5.0
SERVER_POLL_INTERVAL = 0.1

_server_started = False
_server_thread = None


def _start_server_once():
    """Поднять RPC-сервер в фоновом потоке."""
    global _server_started, _server_thread
    if _server_started:
        return
    _server_thread = threading.Thread(
        target=serve_forever, daemon=True
    )
    _server_thread.start()
    deadline = time.time() + SERVER_STARTUP_TIMEOUT
    while time.time() < deadline:
        try:
            with socket.create_connection(
                (HOST, PORT), timeout=0.2
            ):
                break
        except OSError:
            time.sleep(SERVER_POLL_INTERVAL)
    else:
        raise RuntimeError(
            "RPC server did not start in time"
        )
    _server_started = True


def _norm(x):
    """Привести tuple/list к списку для сравнения."""
    if isinstance(x, (list, tuple)):
        return [_norm(i) for i in x]
    return x


class Variant12Machine(RuleBasedStateMachine):
    """Сравниваем RPC и локальную модель."""

    def __init__(self):
        """Сброс локальной модели."""
        super().__init__()
        self.client = RPCClient()
        local.reset()

    def _assert_equal(self, rpc_result, local_result):
        """Проверка равенства результатов."""
        assert _norm(rpc_result) == _norm(local_result), (
            f"mismatch:\n"
            f" RPC   = {rpc_result}\n"
            f" local = {local_result}"
        )

    @rule(
        identifier=st.integers(
            min_value=1000, max_value=9999
        ),
        datetime=st.integers(
            min_value=0, max_value=10_000
        ),
        locale=st.sampled_from(
            ["ru_RU", "en_US", "de_DE"]
        ),
        platform=st.sampled_from(
            ["windows", "linux", "macos"]
        ),
    )
    def create_participant(self, identifier, datetime,
                           locale, platform):
        """Создать Participant на обеих системах."""
        args = dict(
            identifier=identifier,
            datetime=datetime,
            locale=locale,
            platform=platform,
        )
        try:
            rpc_res = self.client.create_participant(**args)
            local_res = local.create_participant(**args)
            self._assert_equal(rpc_res, local_res)
        except (ValueError, RuntimeError):
            try:
                local.create_participant(**args)
                raise AssertionError(
                    "local should have raised"
                )
            except ValueError:
                pass

    @rule()
    def get_participants(self):
        """Прочитать всех участников."""
        self._assert_equal(
            self.client.get_participants(),
            local.get_participants(),
        )

    @precondition(lambda self: local.participants)
    @rule(data=st.data())
    def get_participant(self, data):
        """Прочитать одного участника по id."""
        pid = data.draw(
            st.sampled_from(
                [p[0] for p in local.participants]
            )
        )
        self._assert_equal(
            self.client.get_participant(identifier=pid),
            local.get_participant(pid),
        )

    @precondition(lambda self: local.participants)
    @rule(
        data=st.data(),
        new_locale=st.sampled_from(["ru_RU", "en_US"]),
    )
    def edit_participant(self, data, new_locale):
        """Изменить locale у случайного участника."""
        pid = data.draw(
            st.sampled_from(
                [p[0] for p in local.participants]
            )
        )
        self._assert_equal(
            self.client.edit_participant(
                identifier=pid, locale=new_locale
            ),
            local.edit_participant(
                pid, locale=new_locale
            ),
        )

    @precondition(lambda self: local.participants)
    @rule(
        identifier=st.integers(
            min_value=10000, max_value=19999
        ),
        datetime=st.integers(
            min_value=0, max_value=10_000
        ),
        input_=st.text(min_size=1, max_size=10),
        tags=st.text(min_size=0, max_size=5),
        stage=st.sampled_from(
            ["new", "in_progress", "done"]
        ),
        data=st.data(),
    )
    def create_assignment(self, identifier, datetime,
                          input_, tags, stage, data):
        """Создать Assignment на обеих системах."""
        participant = data.draw(
            st.sampled_from(
                [p[0] for p in local.participants]
            )
        )
        args = dict(
            identifier=identifier,
            datetime=datetime,
            input=input_,
            participant=participant,
            tags=tags,
            stage=stage,
        )
        try:
            rpc_res = self.client.create_assignment(**args)
            local_res = local.create_assignment(**args)
            self._assert_equal(rpc_res, local_res)
        except (ValueError, RuntimeError):
            try:
                local.create_assignment(**args)
                raise AssertionError(
                    "local should have raised"
                )
            except ValueError:
                pass

    @rule()
    def get_assignments(self):
        """Прочитать все задания."""
        self._assert_equal(
            self.client.get_assignments(),
            local.get_assignments(),
        )

    @precondition(lambda self: local.assignments)
    @rule(data=st.data())
    def get_assignment(self, data):
        """Прочитать одно задание по id."""
        aid = data.draw(
            st.sampled_from(
                [a[0] for a in local.assignments]
            )
        )
        self._assert_equal(
            self.client.get_assignment(identifier=aid),
            local.get_assignment(aid),
        )

    @precondition(lambda self: local.assignments)
    @rule(
        data=st.data(),
        new_stage=st.sampled_from(["new", "done"]),
    )
    def edit_assignment(self, data, new_stage):
        """Изменить stage у случайного задания."""
        aid = data.draw(
            st.sampled_from(
                [a[0] for a in local.assignments]
            )
        )
        self._assert_equal(
            self.client.edit_assignment(
                identifier=aid, stage=new_stage
            ),
            local.edit_assignment(
                aid, stage=new_stage
            ),
        )

    @precondition(lambda self: local.assignments)
    @rule(
        identifier=st.integers(
            min_value=20000, max_value=29999
        ),
        datetime=st.integers(
            min_value=0, max_value=10_000
        ),
        response=st.text(min_size=0, max_size=10),
        stage=st.sampled_from(["pending", "done"]),
        cache_hit=st.integers(
            min_value=0, max_value=1
        ),
        data=st.data(),
    )
    def create_result(self, identifier, datetime,
                      response, stage, cache_hit, data):
        """Создать Result на обеих системах."""
        assignment = data.draw(
            st.sampled_from(
                [a[0] for a in local.assignments]
            )
        )
        args = dict(
            identifier=identifier,
            datetime=datetime,
            response=response,
            stage=stage,
            exception="",
            assignment=assignment,
            cache_hit=cache_hit,
        )
        try:
            rpc_res = self.client.create_result(**args)
            local_res = local.create_result(**args)
            self._assert_equal(rpc_res, local_res)
        except (ValueError, RuntimeError):
            try:
                local.create_result(**args)
                raise AssertionError(
                    "local should have raised"
                )
            except ValueError:
                pass

    @rule()
    def get_results(self):
        """Прочитать все результаты."""
        self._assert_equal(
            self.client.get_results(),
            local.get_results(),
        )

    @precondition(lambda self: local.results)
    @rule(data=st.data())
    def get_result(self, data):
        """Прочитать один результат по id."""
        rid = data.draw(
            st.sampled_from(
                [r[0] for r in local.results]
            )
        )
        self._assert_equal(
            self.client.get_result(identifier=rid),
            local.get_result(rid),
        )

    @precondition(lambda self: local.results)
    @rule(
        data=st.data(),
        new_hit=st.integers(min_value=0, max_value=1),
    )
    def edit_result(self, data, new_hit):
        """Изменить cache_hit у случайного результата."""
        rid = data.draw(
            st.sampled_from(
                [r[0] for r in local.results]
            )
        )
        self._assert_equal(
            self.client.edit_result(
                identifier=rid, cache_hit=new_hit
            ),
            local.edit_result(rid, cache_hit=new_hit),
        )

    @rule(
        now=st.integers(min_value=0, max_value=20_000)
    )
    def recent_input_platform_cache_hit(self, now):
        """Специальная выборка."""
        self._assert_equal(
            self.client.recent_input_platform_cache_hit(
                now=now
            ),
            local.recent_input_platform_cache_hit(now),
        )

    def teardown(self):
        """Сбросить локальную модель."""
        local.reset()


def test_mbt():
    """Точка входа MBT."""
    _start_server_once()
    run_state_machine_as_test(
        Variant12Machine,
        settings=settings(
            max_examples=30,
            stateful_step_count=20,
            suppress_health_check=[
                HealthCheck.too_slow,
                HealthCheck.data_too_large,
            ],
            deadline=None,
        ),
    )
