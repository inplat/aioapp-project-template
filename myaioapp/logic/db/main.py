from typing import List
from datetime import datetime
from aioapp.tracer import Span
from ._pg_result import Result, DbType


class GetDate(Result):
    now: datetime

    __sql__ = 'SELECT NOW() as now'

    @classmethod
    async def exec(cls, ctx: Span, db: DbType) -> 'GetDate':
        params = ()
        return await Result._query_one(cls, ctx, db, params)


class GetWeek(Result):
    date: datetime

    __sql__ = """\
        SELECT
            date
        FROM 
            generate_series(
                NOW() - '6day'::interval,
                NOW(),
                '1day'::interval
            ) as date
    """

    @classmethod
    async def exec(cls, ctx: Span, db: DbType) -> List['GetWeek']:
        params = ()
        return await Result._query_all(cls, ctx, db, params)


class UpdateSomeTable(Result):
    __sql__ = """\
        UPDATE
            some_table
        SET
            some_field=1
        WHERE
            id=$1
    """

    @classmethod
    async def exec(cls, ctx: Span, db: DbType, id: int) -> None:
        params = (id,)
        await Result._execute(cls, ctx, db, params)
