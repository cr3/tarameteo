"""Message queue abstraction."""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from typing import Any, Generic, TypeVar

from attrs import define, field

T = TypeVar("T")


class MessageQueue(Generic[T], ABC):
    """Abstract base class for message queues."""

    @abstractmethod
    async def publish(self, topic: str, message: T) -> None:
        """Publish a message to a topic."""

    @abstractmethod
    async def subscribe(self, topic: str) -> AsyncIterator[T]:
        """Subscribe to messages from a topic."""

    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""


@define(frozen=True)
class AsyncioQueue(MessageQueue[T]):
    """Message queue implementation using asyncio.Queue."""

    _queues: dict[str, set[asyncio.Queue[T]]] = field(
        factory=lambda: {"all": set()},
        init=False,
    )

    async def publish(self, topic: str, message: T) -> None:
        """Publish a message to a topic."""
        # Send to topic-specific queues
        topic_queues = self._queues.get(topic, set())
        for queue in topic_queues:
            await queue.put(message)

        # Also send to 'all' topic if this isn't already the 'all' topic
        if topic != "all":
            for queue in self._queues["all"]:
                await queue.put(message)

    async def subscribe(self, topic: str) -> AsyncIterator[T]:
        """Subscribe to messages from a topic."""
        queue = asyncio.Queue[T]()
        try:
            if topic not in self._queues:
                self._queues[topic] = set()
            self._queues[topic].add(queue)

            while True:
                message = await queue.get()
                yield message
        finally:
            # Safe cleanup - topic might have been deleted already
            if topic in self._queues:
                self._queues[topic].discard(queue)
                if not self._queues[topic]:
                    del self._queues[topic]

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        if topic in self._queues:
            del self._queues[topic]


@define(frozen=True)
class QueueManager(Generic[T]):
    """Manager for message queues."""

    _queue: MessageQueue[T] = field()

    async def publish(self, topic: str, message: T) -> None:
        """Publish a message to a topic."""
        await self._queue.publish(topic, message)

    async def stream_messages(
        self,
        topic: str,
        on_message: Callable[[T], Any],
        on_error: Callable[[Exception], Any] | None = None,
    ) -> None:
        """Stream messages from a topic."""
        try:
            async for message in self._queue.subscribe(topic):
                try:
                    await on_message(message)
                except Exception as e:
                    if on_error is not None:
                        await on_error(e)
                    else:
                        raise
        finally:
            await self._queue.unsubscribe(topic)
