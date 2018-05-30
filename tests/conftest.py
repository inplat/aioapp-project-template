import gc
import os
import shutil
import time
import tempfile
import logging
import aiohttp
import asyncio
from functools import partial
import pytest
from yarl import URL
from aiohttp import web
from aiohttp.test_utils import TestServer
import aioamqp
import aioamqp.channel
import aioamqp.protocol
import aioamqp.envelope
import aioamqp.properties
import aiohttp.web
import asyncpg

from .misc import get_free_port, DbClient
from myaioapp.app import Application
from myaioapp.config import Config
from compose.service import ImageType
from compose.project import Project

aioamqp.channel.logger.level = logging.CRITICAL
aioamqp.protocol.logger.level = logging.CRITICAL

pytest_plugins = ["docker_compose"]

COMPOSE_POSTGRES_URL = 'postgres://postgres@127.0.0.1:45432/postgres'
COMPOSE_RABBIT_URL = 'amqp://guest:guest@127.0.0.1:45672/'


def pytest_addoption(parser):
    parser.addoption("--tracer-addr", dest="tracer_addr",
                     help="Use this tracer instead of emulator if specified",
                     metavar="host:port")
    parser.addoption("--metrics-addr", dest="metrics_addr",
                     help="Use this metrics collector instead of emulator if "
                          "specified",
                     metavar="scheme://host:port")
    parser.addoption("--postgres-addr", dest="postgres_addr",
                     help="Postgres connection string",
                     metavar="postgres://user:pwd@host:port/dbname")
    parser.addoption("--rabbit-addr", dest="rabbit_addr",
                     help="RabbitMq connection string",
                     metavar="amqp://user:pass@host:port/vhost")
    parser.addoption('--show-docker-logs', dest="show_docker_logs",
                     action='store_true', default=False,
                     help='Show docker logs after test')


@pytest.fixture(scope='session')
def tracer_override_addr(request):
    return request.config.getoption('tracer_addr')


@pytest.fixture(scope='session')
def metrics_override_addr(request):
    return request.config.getoption('metrics_addr')


@pytest.fixture(scope='session')
def postgres_override_addr(request):
    return request.config.getoption('postgres_addr')


@pytest.fixture(scope='session')
def rabbit_override_addr(request):
    return request.config.getoption('rabbit_addr')


@pytest.fixture(scope='session')
def event_loop():
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    gc.collect()
    loop.close()


@pytest.fixture(scope='session')
def loop(event_loop):
    return event_loop


@pytest.fixture(scope='session')
async def compose(loop,
                  request,
                  docker_project: Project,
                  postgres_override_addr,
                  rabbit_override_addr):
    async def check_postgres(url):
        conn = await asyncpg.connect(url, loop=loop)
        await conn.close()

    async def check_rabbit(url):
        transport, protocol = await aioamqp.from_url(url, loop=loop)
        await protocol.close()

    # async def check_redis(url):
    #     conn = await aioredis.create_connection(url)
    #     conn.close()

    # async def check_http(url):
    #     async with aiohttp.ClientSession(loop=loop) as ses:
    #         resp = await ses.get(url)
    #         assert resp.status == 200

    checks = {
        (
            'postgres',
            'DB_URL',
            postgres_override_addr,
            COMPOSE_POSTGRES_URL,
            check_postgres
        ),
        (
            'rabbit',
            'RABBIT_URL',
            rabbit_override_addr,
            COMPOSE_RABBIT_URL,
            check_rabbit
        ),
    }

    result = {}

    fns = []
    to_start = []
    urls = []
    for svc, name, override, url, fn in checks:
        if override:
            result[name] = override
        else:
            to_start.append(svc)
            urls.append(url)
            fns.append((fn, url))
            result[name] = url

    if not to_start:
        yield result
    else:
        containers = docker_project.up(to_start)

        if not containers:
            raise ValueError("`docker-compose` didn't launch any containers!")

        try:
            timeout = 60
            start_time = time.time()
            print()
            print('Waiting for docker services...')
            print('\n'.join(urls))
            last_err = None
            while start_time + timeout > time.time():
                try:
                    await asyncio.gather(*[fn(url) for fn, url in fns],
                                         loop=loop)
                    break

                except Exception as err:
                    last_err = err
                    await asyncio.sleep(1, loop=loop)
            else:
                last_err_type = type(last_err)
                raise TimeoutError(f'Unable to start all container services'
                                   f' within {timeout} seconds. Last error:'
                                   f' {last_err} ({last_err_type})')
            print('Docker services are ready')
            yield result
        finally:

            # Send container logs to stdout, so that they get included in
            # the test report.
            # https://docs.pytest.org/en/latest/capture.html
            for container in sorted(containers, key=lambda c: c.name):
                if request.config.getoption('show_docker_logs'):
                    header = f"Logs from {container.name}:"
                    print(header)
                    print("=" * len(header))
                    print(
                        container.logs().decode("utf-8", errors="replace") or
                        "(no logs)"
                    )
                    print()

            docker_project.down(ImageType.none, False)


@pytest.fixture(scope='session')
async def tracer_server(loop, tracer_override_addr):
    url = 'http://%s:%s/'
    if tracer_override_addr:
        yield url % tuple(tracer_override_addr.split(':'))
        return

    def tracer_handle(request):
        return web.Response(text='', status=201)

    servers = []
    app = web.Application()
    app.router.add_post('/api/v2/spans', tracer_handle)
    server = TestServer(app, port=None)
    await server.start_server(loop=loop)
    servers.append(server)

    yield url % ('127.0.0.1', server.port)

    while servers:
        await servers.pop().close()


@pytest.fixture(scope='session')
def metrics_server(loop, metrics_override_addr):
    url = '%s://%s:%s'
    if metrics_override_addr:
        addr = URL(metrics_override_addr)
        yield url % (
            addr.scheme or 'udp',
            addr.host or '127.0.0.1',
            addr.port or 8094,
        )
        return

    class TelegrafProtocol:
        def connection_made(self, transport):
            self.transport = transport

        def datagram_received(self, data, addr):
            # print('TELEGRAF received', data, 'from', addr)
            pass

    scheme = 'udp'
    host = '127.0.0.1'
    port = get_free_port(scheme)

    listen = loop.create_datagram_endpoint(
        TelegrafProtocol, local_addr=(host, port))
    transport, protocol = loop.run_until_complete(listen)

    yield url % (scheme, host, port)

    transport.close()


def collect_err(self, err):
    self.errors.append(err)


@pytest.fixture(scope='session')
async def server(loop, compose,
                 tracer_server, metrics_server):
    host = '127.0.0.1'
    port = 10401  # get_free_port()
    print('Starting application')

    build_dir = tempfile.TemporaryDirectory().name
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    env = {
        'HOST': host,
        'PORT': port,
        'TRACER': 'zipkin',
        'TRACER_URL': tracer_server,
        'TRACER_SVC_NAME': 'myaioapp',
        'METRICS': 'telegraf-influx',
        'METRICS_URL': metrics_server,
        'METRICS_SVC_NAME': 'myaioapp_',

    }
    env.update(compose)
    print('\n'.join(['%s=%s' % (k, env[k]) for k in sorted(env.keys())]))

    config = Config(env)
    app = Application(loop=loop, config=config)

    await app.run_prepare()

    app.errors = []
    app.log_err = partial(collect_err, app)

    yield app
    await app.run_shutdown()

    if not os.path.exists(build_dir):
        shutil.rmtree(build_dir)


@pytest.fixture(scope='session')
async def client(loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        yield client


@pytest.fixture(scope='session')
async def db_client(loop, compose):
    async with DbClient(loop, compose['DB_URL']) as cl:
        yield cl
