"""WebSocket connection handler at /live.

One coroutine per connected client. Reads optional subscription messages
from the client and otherwise just forwards readings published by the
broadcaster.
"""
from __future__ import annotations

import asyncio
import json


async def live(websocket, path: str) -> None:
    """Handle one WebSocket client connection.

    Protocol on this socket (JSON frames):
      Client -> Server (optional, after upgrade):
          {"action": "subscribe", "sensors": ["sensor-a", "sensor-b"]}
      Server -> Client (continuous):
          {"sensor_id": "...", "type": "...", "value": ..., "ts": ...}
    """

    broadcaster = websocket.server.broadcaster

    # Queue for this client
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    # None means receive all sensors
    subscriptions: set[str] | None = None

    # Register this client with the broadcaster
    await broadcaster.register(queue)

    print("[WS CONNECTED] Client connected")

    async def sender() -> None:
        """Forward readings from queue to websocket."""
        while True:
            reading = await queue.get()

            sensor_id = reading.get("sensor_id")

            # Filter if subscribed to specific sensors
            if subscriptions is not None:
                if sensor_id not in subscriptions:
                    continue

            await websocket.send(
                json.dumps(
                    {
                        "sensor_id": reading.get("sensor_id"),
                        "type": reading.get("reading_type"),
                        "value": reading.get("value"),
                        "unit": reading.get("unit"),
                        "ts": reading.get("timestamp"),
                    }
                )
            )

    async def receiver() -> None:
        """Handle incoming subscription messages."""
        nonlocal subscriptions

        async for message in websocket:

            try:
                payload = json.loads(message)

                action = payload.get("action")

                if action == "subscribe":
                    sensors = payload.get("sensors", [])

                    subscriptions = set(sensors)

                    await websocket.send(
                        json.dumps(
                            {
                                "status": "subscribed",
                                "sensors": sensors,
                            }
                        )
                    )

            except Exception as e:
                await websocket.send(
                    json.dumps(
                        {
                            "error": str(e)
                        }
                    )
                )

    sender_task = asyncio.create_task(sender())
    receiver_task = asyncio.create_task(receiver())

    try:
        done, pending = await asyncio.wait(
            [sender_task, receiver_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

    finally:
        # Unregister cleanly
        await broadcaster.unregister(queue)

        print("[WS DISCONNECTED] Client disconnected")