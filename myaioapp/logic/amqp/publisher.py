from typing import Optional
from aioapp.tracer import Span
from aioapp.amqp import Channel, AmqpTracerConfig
from aioamqp.channel import Channel as AmqpChannel


class TracerConfig(AmqpTracerConfig):

    def __init__(self, channel: 'AmqpPublisherChannel') -> None:
        super(TracerConfig, self).__init__()
        self.channel = channel

    def on_publish_start(self, ctx: Span,
                         channel: AmqpChannel, payload: bytes,
                         exchange_name: str, routing_key: str,
                         properties: Optional[dict], mandatory: bool,
                         immediate: bool) -> None:
        super(TracerConfig, self).on_publish_start(ctx, channel,
                                                   payload, exchange_name,
                                                   routing_key, properties,
                                                   mandatory, immediate)


class AmqpPublisherChannel(Channel):
    name = 'publisher'

    async def start(self):
        await self.open()

    async def publish(self, ctx: Span, payload: bytes,
                      exchange_name: str, routing_key: str,
                      properties: Optional[dict] = None,
                      mandatory: bool = False, immediate: bool = False,
                      tracer_config: Optional[AmqpTracerConfig] = None,
                      propagate_trace: bool = True, retry: bool = True
                      ) -> None:
        await super().publish(ctx, payload,
                              exchange_name, routing_key,
                              properties,
                              mandatory, immediate,
                              tracer_config or TracerConfig(self),
                              propagate_trace, retry)
