"""Single-sensor simulation logic."""

from __future__ import annotations

import asyncio
import random
import struct
import time

from proto import telemetry_pb2


class SensorSimulator:
    """Simulates one sensor pushing readings to the telemetry server."""

    def __init__(
        self,
        sensor_id: str,
        sensor_type: str,
        interval_seconds: float,
        host: str,
        port: int,
    ) -> None:

        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.interval_seconds = interval_seconds
        self.host = host
        self.port = port

    async def run(self) -> None:
        """Connect, then push readings forever."""

        backoff = 3

        while True:
            try:
                print(f"[{self.sensor_id}] Connecting to server...")

                reader, writer = await asyncio.open_connection(
                    self.host,
                    self.port
                )

                print(f"[{self.sensor_id}] Connected.")

                while True:

                    reading = self._generate_reading()

                    # Serialize protobuf
                    payload = reading.SerializeToString()

                    # Length-prefixed frame
                    frame = struct.pack("!I", len(payload)) + payload

                    writer.write(frame)

                    await writer.drain()

                    # Cleaner display name
                    display_type = reading.reading_type.replace(
                        "soil_moisture",
                        "moisture"
                    )

                    # Print sensor reading
                    print(
                        f"[{self.sensor_id:<8}] "
                        f"{display_type:<12} = "
                        f"{reading.value:.2f} {reading.unit}"
                    )

                    # Add separator after soil sensor
                    if self.sensor_type == "soil_moisture":
                        print(
                            "\n----------------------------------------\n"
                        )

                    await asyncio.sleep(self.interval_seconds)

            except Exception as e:
                print(f"[{self.sensor_id}] Connection error: {e}")

                print(
                    f"[{self.sensor_id}] "
                    f"Reconnecting in {backoff} seconds..."
                )

                await asyncio.sleep(backoff)

    def _generate_reading(self):
        """Generate a realistic reading."""

        reading = telemetry_pb2.Reading()

        reading.sensor_id = self.sensor_id
        reading.reading_type = self.sensor_type
        reading.timestamp = int(time.time())

        if self.sensor_type == "temperature":
            reading.value = round(random.uniform(18, 35), 2)
            reading.unit = "C"

        elif self.sensor_type == "humidity":
            reading.value = round(random.uniform(40, 90), 2)
            reading.unit = "%"

        elif self.sensor_type == "soil_moisture":
            reading.value = round(random.uniform(20, 80), 2)
            reading.unit = "%"

        elif self.sensor_type == "light":
            reading.value = round(random.uniform(100, 1000), 2)
            reading.unit = "lux"

        else:
            reading.value = 0
            reading.unit = "unknown"

        return reading