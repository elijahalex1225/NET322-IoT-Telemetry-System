"""Tracks connected WebSocket clients and dispatches readings to them.

Owns the set of live clients, their subscription filters, and a way for
producers (the telemetry server) to publish a new reading.
"""
from __future__ import annotations

import asyncio
import json


class Broadcaster:
    """Fan-out of readings to the set of connected WebSocket clients."""

    def __init__(self) -> None:
        # websocket -> subscription set | None
        # None means receive all sensors
        self._clients: dict = {}

        # Prevent concurrent modification while publishing
        self._lock = asyncio.Lock()

    async def register(self, websocket) -> None:
        """Add a newly connected client."""
        async with self._lock:
            self._clients[websocket] = None

        print("[BROADCASTER] Client registered")

    async def unregister(self, websocket) -> None:
        """Remove a disconnected client."""
        async with self._lock:
            self._clients.pop(websocket, None)

        print("[BROADCASTER] Client unregistered")

    async def set_subscription(self, websocket, sensor_ids) -> None:
        """Replace the per-client sensor-id filter."""
        async with self._lock:
            if websocket in self._clients:
                self._clients[websocket] = set(sensor_ids)

    async def publish(self, reading) -> None:
        """Push a reading to every interested client.

        Slow-consumer strategy:
            - Each send is protected with a timeout.
            - Slow or disconnected clients are removed.
            - One blocked client never stalls others because all sends
              happen concurrently.
        """

        message = json.dumps(
            {
                "sensor_id": reading.get("sensor_id"),
                "type": reading.get("reading_type"),
                "value": reading.get("value"),
                "unit": reading.get("unit"),
                "ts": reading.get("timestamp"),
            }
        )

        async with self._lock:
            clients_snapshot = list(self._clients.items())

        async def send_to_client(
            websocket,
            subscriptions,
        ) -> None:
            sensor_id = reading.get("sensor_id")

            # Skip if client subscribed to specific sensors
            if subscriptions is not None:
                if sensor_id not in subscriptions:
                    return

            try:
                await asyncio.wait_for(
                    websocket.send(message),
                    timeout=2.0,
                )

            except Exception:
                # Remove dead or slow client
                await self.unregister(websocket)

                try:
                    await websocket.close()
                except Exception:
                    pass

        await asyncio.gather(
            *[
                send_to_client(ws, subscriptions)
                for ws, subscriptions in clients_snapshot
            ],
            return_exceptions=True,
        )