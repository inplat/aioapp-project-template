import asyncio
from typing import Optional
from aioapp.tracer import Span
from aioapp.amqp import Channel, AmqpTracerConfig
from aioamqp.channel import Channel as AmqpChannel
from aioamqp.properties import Properties as AmqpProperties
from aioamqp.envelope import Envelope as AmqpEnvelope


class TracerConfig(AmqpTracerConfig):

    def __init__(self, channel: 'AmqpConsumerChannel') -> None:
        super(TracerConfig, self).__init__()
        self.channel = channel

    def on_ack_start(self, context_span: Span,
                     channel: AmqpChannel,
                     delivery_tag: str, multiple: bool):
        super(TracerConfig, self).on_ack_start(context_span, channel,
                                               delivery_tag, multiple)

    # def on_nack_start(self, context_span: Span,
    #                   channel: AmqpChannel,
    #                   delivery_tag: str, multiple: bool):
    #     super(TracerConfig, self).on_nack_start(context_span, channel,
    #                                             delivery_tag, multiple)


class AmqpConsumerChannel(Channel):
    name = 'consumer'
    queue: Optional[str]
    message_counter: int = 0

    async def start(self):
        await self.open()
        queue = await self._safe_declare_queue('', exclusive=True)
        self.queue = queue['queue']
        await self.consume(self.msg, self.queue)

    async def msg(self, context_span: Span,
                  channel: AmqpChannel,
                  body: bytes,
                  envelope: AmqpEnvelope,
                  properties: AmqpProperties) -> None:
        await self.ack(context_span, envelope.delivery_tag,
                       tracer_config=TracerConfig(self))
        await asyncio.sleep(1, loop=self.amqp.loop)
        self.message_counter += 1
        print('MESSAGE', body)
