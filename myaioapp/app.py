from datetime import timedelta
import asyncio
from typing import Optional, List, Union
import aioapp
from myaioapp.config import Config
from myaioapp.logic.http import MainHttpHandler
from myaioapp.logic.amqp import AmqpConsumerChannel, AmqpPublisherChannel

HTTP_SERVER = 'http_server'
POSTGRES = 'postgres'
RABBIT = 'rabbit'


class Application(aioapp.app.Application):
    def __init__(self, config: Config,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        super(Application, self).__init__(loop)
        self.config = config
        # -------------- HTTP SERVER --------------
        self.add(
            HTTP_SERVER,
            aioapp.http.Server(
                config.http_host,
                config.http_port,
                MainHttpHandler
            )
        )
        # -------------- RABBIT --------------
        _rmqma = self.config.rabbit_prepare_connect_max_attempts
        _rmqri = self.config.rabbit_prepare_connect_retry_interval
        self.add(
            RABBIT,
            aioapp.amqp.Amqp(
                url=self.config.rabbit_url,
                channels=[
                    AmqpConsumerChannel(),
                    AmqpPublisherChannel(),
                ],
                heartbeat=self.config.rabbit_heartbeat,
                connect_max_attempts=_rmqma,
                connect_retry_delay=_rmqri
            ),
            stop_after=[HTTP_SERVER]
        )
        # -------------- POSTGRS --------------
        _pglt = self.config.db_pool_max_inactive_connection_lifetime
        _pgma = self.config.db_prepare_connect_max_attempts
        _pgri = self.config.db_prepare_connect_retry_interval
        self.add(
            POSTGRES,
            aioapp.db.Postgres(
                url=self.config.db_url,
                pool_min_size=self.config.db_pool_min_size,
                pool_max_size=self.config.db_pool_max_size,
                pool_max_queries=self.config.db_pool_max_queries,
                pool_max_inactive_connection_lifetime=_pglt,
                connect_max_attempts=_pgma,
                connect_retry_delay=_pgri
            ),
            stop_after=[HTTP_SERVER, RABBIT]
        )
        self.setup_logging(
            tracer_driver=config.tracer_driver,
            tracer_name=config.tracer_name,
            tracer_addr=config.tracer_url,
            tracer_default_sampled=config.tracer_default_sampled,
            metrics_driver=config.metrics_driver,
            metrics_addr=config.metrics_url,
            metrics_name=config.metrics_name
        )

    @property
    def http_server(self) -> aioapp.http.Server:
        return self._components[HTTP_SERVER]  # type: ignore

    @property
    def db(self) -> aioapp.db.Postgres:
        return self._components[POSTGRES]  # type: ignore

    @property
    def rmq(self) -> aioapp.amqp.Amqp:
        return self._components[RABBIT]  # type: ignore

    @property
    def rmq_publisher(self) -> AmqpPublisherChannel:
        return self.rmq.channel(AmqpPublisherChannel.name)  # type: ignore

    @property
    def rmq_consumer(self) -> AmqpConsumerChannel:
        return self.rmq.channel(AmqpConsumerChannel.name)  # type: ignore
