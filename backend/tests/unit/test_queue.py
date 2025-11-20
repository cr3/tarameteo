"""Tests for queue module."""

import asyncio
from datetime import datetime

import pytest
from pydantic import BaseModel

from tarameteo.queue import AsyncioQueue, QueueManager


class Message(BaseModel):
    """Test message model."""

    content: str
    timestamp: datetime


@pytest.fixture
def queue() -> AsyncioQueue[Message]:
    """Create a test queue."""
    return AsyncioQueue[Message]()


@pytest.fixture
def manager(queue: AsyncioQueue[Message]) -> QueueManager[Message]:
    """Create a test queue manager."""
    return QueueManager(queue)


@pytest.mark.asyncio
async def test_publish_subscribe(queue: AsyncioQueue[Message]) -> None:
    """Test publishing and subscribing to messages."""
    message = Message(content="test", timestamp=datetime.now())
    received_messages: list[Message] = []

    async def collect_messages() -> None:
        async for msg in queue.subscribe("test_topic"):
            received_messages.append(msg)
            if len(received_messages) == 2:
                break

    # Start subscriber
    subscriber = asyncio.create_task(collect_messages())
    await asyncio.sleep(0)  # Let subscriber start

    # Publish messages
    await queue.publish("test_topic", message)
    await queue.publish("test_topic", message)

    # Wait for subscriber to collect messages
    await subscriber
    assert len(received_messages) == 2
    assert all(msg == message for msg in received_messages)


@pytest.mark.asyncio
async def test_multiple_topics(queue: AsyncioQueue[Message]) -> None:
    """Test publishing to multiple topics."""
    message1 = Message(content="test1", timestamp=datetime.now())
    message2 = Message(content="test2", timestamp=datetime.now())
    received_messages: list[Message] = []

    async def collect_messages() -> None:
        async for msg in queue.subscribe("all"):
            received_messages.append(msg)
            if len(received_messages) == 2:
                break

    # Start subscriber
    subscriber = asyncio.create_task(collect_messages())
    await asyncio.sleep(0)  # Let subscriber start

    # Publish to different topics
    await queue.publish("topic1", message1)
    await queue.publish("topic2", message2)

    # Wait for subscriber to collect messages
    await subscriber
    assert len(received_messages) == 2
    assert received_messages[0] == message1
    assert received_messages[1] == message2


@pytest.mark.asyncio
async def test_unsubscribe(queue: AsyncioQueue[Message]) -> None:
    """Test unsubscribing from a topic."""
    message = Message(content="test", timestamp=datetime.now())
    received_messages: list[Message] = []

    async def collect_messages() -> None:
        async for msg in queue.subscribe("test_topic"):
            received_messages.append(msg)
            await queue.unsubscribe("test_topic")
            break

    # Start subscriber
    subscriber = asyncio.create_task(collect_messages())
    await asyncio.sleep(0)  # Let subscriber start

    # Publish messages
    await queue.publish("test_topic", message)
    await queue.publish("test_topic", message)

    # Wait for subscriber to collect messages
    await subscriber
    assert len(received_messages) == 1
    assert received_messages[0] == message


@pytest.mark.asyncio
async def test_queue_manager_publish(manager: QueueManager[Message]) -> None:
    """Test queue manager publishing."""
    message = Message(content="test", timestamp=datetime.now())
    received_messages: list[Message] = []

    async def on_message(msg: Message) -> None:
        received_messages.append(msg)

    # Start message stream
    stream = asyncio.create_task(
        manager.stream_messages("test_topic", on_message),
    )
    await asyncio.sleep(0)  # Let stream start

    # Publish message
    await manager.publish("test_topic", message)
    await asyncio.sleep(0)  # Let message be processed

    # Cancel stream
    stream.cancel()
    with pytest.raises(asyncio.CancelledError):
        await stream

    assert len(received_messages) == 1
    assert received_messages[0] == message


@pytest.mark.asyncio
async def test_queue_manager_error_handling(manager: QueueManager[Message]) -> None:
    """Test queue manager error handling."""
    message = Message(content="test", timestamp=datetime.now())
    errors: list[Exception] = []

    async def on_message(msg: Message) -> None:
        raise ValueError("Test error")

    async def on_error(error: Exception) -> None:
        errors.append(error)

    # Start message stream with error handling
    stream = asyncio.create_task(
        manager.stream_messages("test_topic", on_message, on_error),
    )
    await asyncio.sleep(0)  # Let stream start

    # Publish message
    await manager.publish("test_topic", message)
    await asyncio.sleep(0)  # Let message be processed

    # Cancel stream
    stream.cancel()
    with pytest.raises(asyncio.CancelledError):
        await stream

    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert str(errors[0]) == "Test error"


@pytest.mark.asyncio
async def test_queue_manager_error_propagation(manager: QueueManager[Message]) -> None:
    """Test queue manager error propagation when no error handler."""
    message = Message(content="test", timestamp=datetime.now())

    async def on_message(msg: Message) -> None:
        raise ValueError("Test error")

    # Start message stream without error handling
    stream = asyncio.create_task(
        manager.stream_messages("test_topic", on_message),
    )
    await asyncio.sleep(0)  # Let stream start

    # Publish message
    await manager.publish("test_topic", message)

    # Wait for the task to complete or raise an exception
    with pytest.raises(ValueError, match="Test error"):
        await stream
