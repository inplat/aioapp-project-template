from aiohttp import ClientSession, web
from asyncpg.exceptions import UndefinedTableError
from myaioapp.app import Application
from .misc import check_app_errors, check_app_raises, wait_for


@check_app_errors
async def test_myaioapp(server: Application, client: ClientSession):
    url = 'http://127.0.0.1:%d/' % server.http_server.port
    resp = await client.get(url)
    assert resp.status == 200
    assert 'Hello, world' in await resp.text()

    async def check():
        if server.rmq_consumer.message_counter == 0:
            raise Exception()

    await wait_for(server, check)
    assert server.rmq_consumer.message_counter == 1


@check_app_errors
async def test_error_handler(server: Application, client: ClientSession):
    url = 'http://127.0.0.1:%d/nof_found_url' % server.http_server.port
    with check_app_raises(server, web.HTTPNotFound):
        resp = await client.get(url)
    assert resp.status == 404
    assert 'Not Found' in await resp.text()


@check_app_errors
async def test_error_internal_error(server: Application,
                                    client: ClientSession):
    url = 'http://127.0.0.1:%d/?error=1' % server.http_server.port
    with check_app_raises(server, UndefinedTableError):
        resp = await client.get(url)
    assert resp.status == 500
    assert 'Internal Server Error' in await resp.text()
