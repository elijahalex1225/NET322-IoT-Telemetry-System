from __future__ import annotations

import asyncio

from aiohttp import web

from server.rest_api import build_app
from server.storage import SQLiteStorage
from server.tcp_ingest import start_tcp_server


async def main() -> None:

    # Initialize SQLite storage
    storage = SQLiteStorage()

    await storage.initialize()

    # Start TCP ingest server
    tcp_server = await start_tcp_server(
        host="0.0.0.0",
        port=9000,
        storage=storage,
        broadcaster=None,
    )

    # Build REST API
    app = build_app(storage)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        8080,
    )

    await site.start()

    print("\n=== IoT Telemetry System Started ===")
    print("REST API : http://127.0.0.1:8080")
    print("TCP Port : 9000")
    print("Waiting for sensor connections..........!\n")

    async with tcp_server:
        await tcp_server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())