"""Точка запуска TCP RPC-сервера"""

from .rpc import serve_forever


if __name__ == "__main__":
    serve_forever()