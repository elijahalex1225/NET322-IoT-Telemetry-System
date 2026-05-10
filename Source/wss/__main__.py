"""Entry point for the WebSocket live-feed server.

Run with:
    python -m wss
"""
from __future__ import annotations

import asyncio
import json
import os

import websockets

from wss.broadcaster import Broadcaster
from wss.handler import live


async def reading_consumer(
    broadcaster: Broadcaster,
    queue: asyncio.Queue,
) -> None:
    """Consume readings from shared queue and publish them."""

    while True:
        reading = await queue.get()

        try:
            await broadcaster.publish(reading)

        finally:
            queue.task_done()


async def main() -> None:
    """Boot the WebSocket server."""

    host = os.getenv("WS_HOST", "0.0.0.0")
    port = int(os.getenv("WS_PORT", "8765"))

    # Shared broadcaster
    broadcaster = Broadcaster()

    # Shared queue used by telemetry server
    reading_queue: asyncio.Queue = asyncio.Queue(
        maxsize=1000
    )

    # Background consumer task
    consumer_task = asyncio.create_task(
        reading_consumer(
            broadcaster,
            reading_queue,
        )
    )

    async def websocket_handler(websocket):

        # Attach broadcaster to server connection
        websocket.server.broadcaster = broadcaster

        await live(websocket, "/live")

    server = await websockets.serve(
        websocket_handler,
        host,
        port,
    )

    print("\n=== WebSocket Live Feed Started ===")
    print(f"1.WebSocket URL : ws://{host}:{port}/live")
    print("2.Waiting for dashboard clients............!\n")

    try:
        # Run forever
        await asyncio.Future()

    finally:
        consumer_task.cancel()

        server.close()

        await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())