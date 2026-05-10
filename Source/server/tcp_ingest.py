
from __future__ import annotations
import asyncio
import struct
from proto import telemetry_pb2


async def handle_sensor(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """Handle one sensor connection until it closes."""

    address = writer.get_extra_info("peername")

    print(f"[CONNECTED] Sensor {address}")

    storage = writer.transport._server.storage
    broadcaster = writer.transport._server.broadcaster

    try:
        while True:

            try:
                # Read frame size
                header = await reader.readexactly(4)

                message_length = struct.unpack("!I", header)[0]

                # Validate frame size
                if message_length <= 0 or message_length > 10_000:
                    raise ValueError(
                        f"Invalid message length: {message_length}"
                    )

                # Read protobuf payload
                payload = await reader.readexactly(message_length)

                # Decode protobuf
                reading = telemetry_pb2.Reading()

                reading.ParseFromString(payload)

                reading_data = {
                    "sensor_id": reading.sensor_id,
                    "reading_type": reading.reading_type,
                    "value": reading.value,
                    "unit": reading.unit,
                    "timestamp": reading.timestamp,
                }

                print(
                    f"[RECEIVED] "
                    f"{reading.sensor_id} | "
                    f"{reading.reading_type} | "
                    f"{reading.value} {reading.unit}"
                )

                # Save reading to database
                if storage is not None:
                    await storage.add_reading(reading_data)

                # Broadcast to websocket clients
                if broadcaster is not None:
                    await broadcaster.broadcast(reading_data)

            except asyncio.IncompleteReadError:
                print(f"[DISCONNECTED] {address}")
                break

            except Exception as e:
                print(f"[MALFORMED MESSAGE] {e}")
                continue

    finally:
        writer.close()
        await writer.wait_closed()


async def start_tcp_server(
    host: str,
    port: int,
    storage,
    broadcaster,
) -> asyncio.AbstractServer:
    """Start TCP ingest server."""

    server = await asyncio.start_server(
        handle_sensor,
        host,
        port,
    )

    # Attach shared services
    server.storage = storage
    server.broadcaster = broadcaster

    print(f"TCP server listening on {host}:{port}")

    return server