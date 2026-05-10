"""Entry point for the sensor simulator.

Run with:
    python -m client --config config/sensors.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import yaml

from client.simulator import SensorSimulator


async def main() -> None:
    """Load YAML config and run all sensors."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="IoT Sensor Simulator"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to sensors YAML config file"
    )

    args = parser.parse_args()

    # Load YAML configuration
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Read server settings
    server_host = config["server"]["host"]
    server_port = config["server"]["port"]

    sensors = config["sensors"]

    tasks = []

    # Create one simulator per sensor
    for sensor in sensors:

        simulator = SensorSimulator(
            sensor_id=sensor["id"],
            sensor_type=sensor["type"],
            interval_seconds=sensor["interval"],
            host=server_host,
            port=server_port,
        )

        tasks.append(
            asyncio.create_task(simulator.run())
        )

    print(f"Starting {len(tasks)} sensors...")

    # Run all sensor tasks forever
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())