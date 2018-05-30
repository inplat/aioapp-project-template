import asyncio
from typing import Union, List, Callable, Optional
import traceback
import socket
import functools
import asyncpg.protocol
from async_timeout import timeout
from myaioapp.app import Application


def get_free_port(protocol='tcp'):
    family = socket.AF_INET
    if protocol == 'tcp':
        type = socket.SOCK_STREAM
    elif protocol == 'udp':
        type = socket.SOCK_DGRAM
    else:
        raise UserWarning()

    sock = socket.socket(family, type)
    try:
        sock.bind(('', 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


def format_errors(errors: List[Union[BaseException, str]]) -> str:
    res = []
    for err in errors:
        if isinstance(err, BaseException):
            fmt = '%s%s: %s' % (
                ''.join(traceback.format_tb(err.__traceback__)),
                err.__class__.__name__,
                err)
            res.append(fmt)
        else:
            res.append(err)
    return ('\n\n%s\n\n' % ('-' * 70)).join(res)


def clean_server_errors(server: Application):
    server.errors = []


def check_server_errors(server: Application):
    assert len(server.errors) == 0, format_errors(server.errors)


def check_app_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        server: Optional[Application] = None
        for arg in list(args) + list(kwargs.values()):
            if isinstance(arg, Application):
                server = arg
                break
        if server is None:
            raise UserWarning('Application instance not found in test '
                              'fixtures')
        clean_server_errors(server)
        try:
            return await func(*args, **kwargs)
        finally:
            check_server_errors(server)

    return wrapper


def check_app_raises(server, err_cls):
    """
    Проверяет была ли ошибка сервера во время выполнения контекста.
    После выполнения удаляет ошибку из лога, т.к. это ожидаемое поведение.
    В противном случае функция check_server_errors не пройдет проверку
    """

    class Context:
        def __init__(self, server, err_cls):
            # check_server_errors(server)
            self.server = server
            self.err_cls = err_cls
            self.errors_cnt = None

        def __enter__(self):
            self.errors_cnt = len(self.server.errors)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            srv_cnt = len(server.errors)
            exp_cnt = self.errors_cnt + 1
            assert srv_cnt == exp_cnt, ('server has %s, expected %s %s'
                                        '' % (srv_cnt, exp_cnt,
                                              self.err_cls.__name__))
            assert isinstance(server.errors[-1], self.err_cls)
            server.errors.pop()

    return Context(server, err_cls)


async def wait_for(server: Application, fn: Callable):
    err = None
    assert asyncio.iscoroutinefunction(fn)
    try:
        with timeout(10, loop=server.loop):
            while True:
                try:
                    return await fn()
                except Exception as e:
                    err = e
                    check_server_errors(server)
                await asyncio.sleep(.05, loop=server.loop)
    except asyncio.TimeoutError:
        if err is not None:
            raise err
        else:
            raise


class DbClient:

    def __init__(self, loop: asyncio.AbstractEventLoop, dsn: str) -> None:
        self.loop = loop
        self.dsn = dsn
        self.conn: asyncpg.Connection = None

    async def connect(self) -> None:
        self.conn = await asyncpg.connect(dsn=self.dsn, loop=self.loop)

    async def disconnect(self) -> None:
        await self.conn.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def execute(self, query: str, *args, timeout: float = None) -> str:
        return await self.conn.execute(query, *args, timeout=timeout)

    async def fetch(self, query, *args, timeout=None) -> list:
        return await self.conn.fetch(query, *args, timeout=timeout)

    async def fetchrow(self, query, *args, timeout=None):
        return await self.conn.fetchrow(query, *args, timeout=timeout)
