from typing import Any, Type, Union, Tuple, Optional
import asyncpg.protocol
from aioapp.tracer import Span
from aioapp.db.postgres import Postgres, Connection, PostgresTracerConfig

DbType = Union[Connection, Postgres]


class TracerConfig(PostgresTracerConfig):

    def on_query_start(self, ctx_span: 'Span', id: str, query: str,
                       args: tuple, timeout: Optional[float]):
        super(TracerConfig, self).on_query_start(ctx_span, id, query,
                                                 args, timeout)


class Result:
    __sql__: str = None

    def __init__(self, **kwargs) -> None:
        self._vals = kwargs
        for key, value in kwargs.items():
            setattr(self, key, self._format(key, value))

    def asdict(self):
        return self._vals

    def _format(self, key: str, val: Any) -> Any:
        return val

    @staticmethod
    async def _execute(cls: Type['Result'], ctx_span: Span,
                       db: DbType,
                       params: Tuple) -> str:
        return await db.execute(ctx_span, cls.__name__, cls.__sql__,
                                *params,
                                tracer_config=TracerConfig())

    @staticmethod
    async def _query_one(cls: Type['Result'], ctx_span: Span,
                         db: DbType,
                         params: Tuple) -> asyncpg.protocol.Record:
        res = await db.query_one(ctx_span, cls.__name__, cls.__sql__,
                                 *params,
                                 tracer_config=TracerConfig())
        return cls(**dict(res)) if res is not None else None

    @staticmethod
    async def _query_all(cls: Type['Result'], ctx_span: Span,
                         db: DbType,
                         params: Tuple) -> asyncpg.protocol.Record:
        res = await db.query_all(ctx_span, cls.__name__, cls.__sql__,
                                 *params,
                                 tracer_config=TracerConfig())
        return [cls(**dict(row)) for row in res] if res is not None else None
