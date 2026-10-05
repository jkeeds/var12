"""Model-Based Testing для RPC"""

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


# --- Сервер в фоне ---

_server_started = False
_server_thread = None


def _start_server_once():
    global _server_started, _server_thread
    if _server_started:
        return
    _server_thread = threading.Thread(target=serve_forever, daemon=True)
    _server_thread.start()
    for _ in range(50):
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError("RPC server did not start in time")
    _server_started = True


# --- Утилита: нормализация tuple/list ---

def _norm(x):
    if isinstance(x, (list, tuple)):
        return [_norm(i) for i in x]
    return x


# --- RuleBasedStateMachine ---

class Variant12Machine(RuleBasedStateMachine):

    def __init__(self):
        super().__init__()
        self.client = RPCClient()
        local.reset()

    def _assert_equal(self, rpc_result, local_result):
        assert _norm(rpc_result) == _norm(local_result), (
            f"mismatch:\n RPC  = {rpc_result}\n local = {local_result}"
        )

    # --- Participant ---

    @rule(
        identifier=st.integers(min_value=1000, max_value=9999),
        datetime=st.integers(min_value=0, max_value=10_000),
        locale=st.sampled_from(["ru_RU", "en_US", "de_DE"]),
        platform=st.sampled_from(["windows", "linux", "macos"]),
    )
    def create_participant(self, identifier, datetime, locale, platform):
        args = dict(identifier=identifier, datetime=datetime,
                    locale=locale, platform=platform)
        try:
            rpc_res = self.client.create_participant(**args)
            local_res = local.create_participant(**args)
            self._assert_equal(rpc_res, local_res)
        except (ValueError, RuntimeError):
            try:
                local.create_participant(**args)
                raise AssertionError("local should have raised")
            except ValueError:
                pass

    @rule()
    def get_participants(self):
        self._assert_equal(self.client.get_participants(),
                           local.get_participants())

    @precondition(lambda self: local.participants)
    @rule(data=st.data())
    def get_participant(self, data):
        pid = data.draw(st.sampled_from([p[0] for p in local.participants]))
        self._assert_equal(self.client.get_participant(identifier=pid),
                           local.get_participant(pid))

    @precondition(lambda self: local.participants)
    @rule(data=st.data(), new_locale=st.sampled_from(["ru_RU", "en_US"]))
    def edit_participant(self, data, new_locale):
        pid = data.draw(st.sampled_from([p[0] for p in local.participants]))
        self._assert_equal(
            self.client.edit_participant(identifier=pid, locale=new_locale),
            local.edit_participant(pid, locale=new_locale),
        )

    # --- Assignment ---

    @precondition(lambda self: local.participants)
    @rule(
        identifier=st.integers(min_value=10000, max_value=19999),
        datetime=st.integers(min_value=0, max_value=10_000),
        input_=st.text(min_size=1, max_size=10),
        tags=st.text(min_size=0, max_size=5),
        stage=st.sampled_from(["new", "in_progress", "done"]),
        data=st.data(),
    )
    def create_assignment(self, identifier, datetime, input_, tags, stage, data):
        participant = data.draw(
            st.sampled_from([p[0] for p in local.participants]))
        args = dict(identifier=identifier, datetime=datetime, input=input_,
                    participant=participant, tags=tags, stage=stage)
        try:
            rpc_res = self.client.create_assignment(**args)
            local_res = local.create_assignment(**args)
            self._assert_equal(rpc_res, local_res)
        except (ValueError, RuntimeError):
            try:
                local.create_assignment(**args)
                raise AssertionError("local should have raised")
            except ValueError:
                pass

    @rule()
    def get_assignments(self):
        self._assert_equal(self.client.get_assignments(),
                           local.get_assignments())

    @precondition(lambda self: local.assignments)
    @rule(data=st.data())
    def get_assignment(self, data):
        aid = data.draw(st.sampled_from([a[0] for a in local.assignments]))
        self._assert_equal(self.client.get_assignment(identifier=aid),
                           local.get_assignment(aid))

    @precondition(lambda self: local.assignments)
    @rule(data=st.data(), new_stage=st.sampled_from(["new", "done"]))
    def edit_assignment(self, data, new_stage):
        aid = data.draw(st.sampled_from([a[0] for a in local.assignments]))
        self._assert_equal(
            self.client.edit_assignment(identifier=aid, stage=new_stage),
            local.edit_assignment(aid, stage=new_stage),
        )

    # --- Result ---

    @precondition(lambda self: local.assignments)
    @rule(
        identifier=st.integers(min_value=20000, max_value=29999),
        datetime=st.integers(min_value=0, max_value=10_000),
        response=st.text(min_size=0, max_size=10),
        stage=st.sampled_from(["pending", "done"]),
        exception=st.text(min_size=0, max_size=5),
        cache_hit=st.integers(min_value=0, max_value=1),
        data=st.data(),
    )
    def create_result(self, identifier, datetime, response, stage,
                      exception, cache_hit, data):
        aid = data.draw(st.sampled_from([a[0] for a in local.assignments]))
        args = dict(identifier=identifier, datetime=datetime,
                    response=response, stage=stage, exception=exception,
                    assignment=aid, cache_hit=cache_hit)
        try:
            rpc_res = self.client.create_result(**args)
            local_res = local.create_result(**args)
            self._assert_equal(rpc_res, local_res)
        except (ValueError, RuntimeError):
            try:
                local.create_result(**args)
                raise AssertionError("local should have raised")
            except ValueError:
                pass

    @rule()
    def get_results(self):
        self._assert_equal(self.client.get_results(), local.get_results())

    @precondition(lambda self: local.results)
    @rule(data=st.data())
    def get_result(self, data):
        rid = data.draw(st.sampled_from([r[0] for r in local.results]))
        self._assert_equal(self.client.get_result(identifier=rid),
                           local.get_result(rid))

    @precondition(lambda self: local.results)
    @rule(data=st.data(), new_hit=st.integers(min_value=0, max_value=1))
    def edit_result(self, data, new_hit):
        rid = data.draw(st.sampled_from([r[0] for r in local.results]))
        self._assert_equal(
            self.client.edit_result(identifier=rid, cache_hit=new_hit),
            local.edit_result(rid, cache_hit=new_hit),
        )

    # --- Специальная выборка ---

    @rule(now=st.integers(min_value=0, max_value=20_000))
    def recent_input_platform_cache_hit(self, now):
        self._assert_equal(
            self.client.recent_input_platform_cache_hit(now=now),
            local.recent_input_platform_cache_hit(now),
        )

    def teardown(self):
        local.reset()


# --- Точка входа ---

def test_mbt():
    _start_server_once()
    run_state_machine_as_test(
        Variant12Machine,
        settings=settings(
            max_examples=30,
            stateful_step_count=20,
            suppress_health_check=[HealthCheck.too_slow,
                                   HealthCheck.data_too_large],
            deadline=None,
        ),
    )