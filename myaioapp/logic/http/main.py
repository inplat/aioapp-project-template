from aiohttp import web
import myaioapp.app  # noqa
from aioapp.http import Handler
from aioapp.tracer import Span
from .. import db


class MainHttpHandler(Handler):

    def __init__(self, server) -> None:
        super().__init__(server)

    @property
    def app(self) -> 'myaioapp.app.Application':
        return self.server.app  # type: ignore

    async def prepare(self):
        self.server.error_handler = self.error_handler
        self.server.add_route('GET', '/', self.home_get_handler)

    async def error_handler(self, ctx: Span,
                            request: web.Request,
                            error: Exception) -> web.Response:
        self.app.log_err(error)
        if isinstance(error, web.HTTPException):
            return error
        return web.HTTPInternalServerError()

    async def home_get_handler(self, ctx: Span,
                               request: web.Request) -> web.Response:
        if request.query.get('error'):
            await db.UpdateSomeTable.exec(ctx, self.app.db, 1)

        if self.app.rmq_consumer.queue is None:  # pragma: nocover
            raise web.HTTPInternalServerError()

        res1 = await db.GetWeek.exec(ctx, self.app.db)
        res2 = await db.GetDate.exec(ctx, self.app.db)

        await self.app.rmq_publisher.publish(ctx, b'test message', '',
                                             self.app.rmq_consumer.queue,
                                             propagate_trace=False)
        return web.Response(
            text='Hello, world!\n'
                 'Now: %s\n'
                 'Week: %s' % (
                     res2.now.isoformat(),
                     ','.join([str(row.asdict()) for row in res1]))
        )
