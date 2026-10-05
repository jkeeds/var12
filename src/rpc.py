"""RPC на основе TCP

Протокол (little-endian):

Запрос:
    [0:1]  код операции (1 байт)
    [1:6]  размер тела запроса (5 байт)
    [6:]   тело (JSON, UTF-8)

Ответ:
    [0:1]  версия протокола (1 байт, = 1)
    [1:2]  код операции (1 байт)
    [2:6]  размер тела ответа (4 байта)
    [6:]   тело (JSON, UTF-8)

Журналирование всех запросов к RPC — в файл journal.log.
"""

import json
import logging
import socket
import struct
from typing import Any

from . import model as m


# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

HOST = "127.0.0.1"
PORT = 9000
PROTOCOL_VERSION = 1

# код операции -> (имя метода, функция модели)
OPERATIONS: dict[int, tuple[str, Any]] = {
    1:  ("create_participant", m.create_participant),
    2:  ("get_participants", m.get_participants),
    3:  ("get_participant", m.get_participant),
    4:  ("edit_participant", m.edit_participant),
    5:  ("create_assignment", m.create_assignment),
    6:  ("get_assignments", m.get_assignments),
    7:  ("get_assignment", m.get_assignment),
    8:  ("edit_assignment", m.edit_assignment),
    9:  ("create_result", m.create_result),
    10: ("get_results", m.get_results),
    11: ("get_result", m.get_result),
    12: ("edit_result", m.edit_result),
    13: ("recent_input_platform_cache_hit", m.recent_input_platform_cache_hit),
}

METHOD_TO_CODE: dict[str, int] = {name: code for code, (name, _) in OPERATIONS.items()}


# ---------------------------------------------------------------------------
# Журналирование
# ---------------------------------------------------------------------------

logger = logging.getLogger("rpc")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler("journal.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)


# ---------------------------------------------------------------------------
# Чтение/запись сокетов
# ---------------------------------------------------------------------------

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """Читает ровно n байт из сокета."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed by peer")
        buf += chunk
    return buf


def _send_request(sock: socket.socket, opcode: int, args: dict) -> dict:
    """Отправляет RPC-запрос и возвращает распарсенный ответ."""
    body = json.dumps(args, ensure_ascii=False).encode("utf-8")

    # код операции (1 байт) + размер тела (5 байт) + тело
    header = struct.pack("<B", opcode) + body.__len__().to_bytes(5, "little")
    sock.sendall(header + body)

    # читаем ответ
    version = _recv_exact(sock, 1)[0]
    code = _recv_exact(sock, 1)[0]
    size = int.from_bytes(_recv_exact(sock, 4), "little")
    resp_body = _recv_exact(sock, size) if size > 0 else b""
    resp = json.loads(resp_body.decode("utf-8")) if resp_body else {}
    return {"version": version, "code": code, **resp}


def _handle_request(opcode: int, args: dict) -> tuple[dict, bool]:
    """Выполняет операцию. Возвращает (ответ, is_ok)."""
    if opcode not in OPERATIONS:
        return {"error": f"unknown opcode {opcode}"}, False
    name, func = OPERATIONS[opcode]
    try:
        result = func(**args)
        return {"result": result}, True
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}, False


# ---------------------------------------------------------------------------
# Сервер
# ---------------------------------------------------------------------------

def serve_forever() -> None:
    """Запускает TCP-сервер."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)
        print(f"RPC server listening on {HOST}:{PORT}")

        while True:
            conn, addr = srv.accept()
            with conn:
                try:
                    _serve_client(conn, addr)
                except ConnectionError:
                    pass


def _serve_client(conn: socket.socket, addr: tuple) -> None:
    """Обслуживает одного клиента (одна операция за соединение)."""
    # код операции — 1 байт
    opcode = _recv_exact(conn, 1)[0]
    # размер тела — 5 байт
    size = int.from_bytes(_recv_exact(conn, 5), "little")
    body = _recv_exact(conn, size) if size > 0 else b""
    args = json.loads(body.decode("utf-8")) if body else {}

    logger.info("REQ opcode=%s args=%s", opcode, args)

    resp, _ = _handle_request(opcode, args)
    resp_body = json.dumps(resp, ensure_ascii=False, default=list).encode("utf-8")

    # заголовок ответа: version(1) + opcode(1) + size(4)
    header = (
        struct.pack("<B", PROTOCOL_VERSION)
        + struct.pack("<B", opcode)
        + len(resp_body).to_bytes(4, "little")
    )
    conn.sendall(header + resp_body)

    logger.info("RESP opcode=%s body=%s", opcode, resp)


# ---------------------------------------------------------------------------
# Клиент
# ---------------------------------------------------------------------------

class RPCClient:
    """Клиент к RPC. Имена методов совпадают с функциями модели."""

    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port

    def _call(self, name: str, **kwargs: Any) -> Any:
        opcode = METHOD_TO_CODE.get(name)
        if opcode is None:
            raise ValueError(f"unknown method '{name}'")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            resp = _send_request(sock, opcode, kwargs)
        if "error" in resp:
            raise RuntimeError(resp["error"])
        return resp.get("result")

    # --- Participant ---
    def create_participant(self, **kw): return self._call("create_participant", **kw)
    def get_participants(self):         return self._call("get_participants")
    def get_participant(self, **kw):    return self._call("get_participant", **kw)
    def edit_participant(self, **kw):   return self._call("edit_participant", **kw)

    # --- Assignment ---
    def create_assignment(self, **kw):  return self._call("create_assignment", **kw)
    def get_assignments(self):          return self._call("get_assignments")
    def get_assignment(self, **kw):     return self._call("get_assignment", **kw)
    def edit_assignment(self, **kw):    return self._call("edit_assignment", **kw)

    # --- Result ---
    def create_result(self, **kw):      return self._call("create_result", **kw)
    def get_results(self):              return self._call("get_results")
    def get_result(self, **kw):         return self._call("get_result", **kw)
    def edit_result(self, **kw):        return self._call("edit_result", **kw)

    # --- Специальная выборка ---
    def recent_input_platform_cache_hit(self, **kw):
        return self._call("recent_input_platform_cache_hit", **kw)