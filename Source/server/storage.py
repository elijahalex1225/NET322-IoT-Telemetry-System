from __future__ import annotations

from typing import Iterable, Optional

import aiosqlite


class Storage:
    """Abstract storage interface."""

    async def add_sensor(self, sensor) -> None:
        raise NotImplementedError

    async def remove_sensor(self, sensor_id: str) -> None:
        raise NotImplementedError

    async def list_sensors(self) -> Iterable:
        raise NotImplementedError

    async def add_reading(self, reading) -> None:
        raise NotImplementedError

    async def get_readings(
        self,
        sensor_id: str,
        from_ts: Optional[float] = None,
        to_ts: Optional[float] = None,
    ) -> Iterable:
        raise NotImplementedError


class SQLiteStorage(Storage):

    def __init__(self, db_path: str = "GreenHouse.db"):
        self.db_path = db_path


    async def initialize(self) -> None:

        async with aiosqlite.connect(self.db_path) as db:

            await db.execute("""
                CREATE TABLE IF NOT EXISTS sensors (
                    id TEXT PRIMARY KEY,
                    type TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT,
                    reading_type TEXT,
                    value REAL,
                    unit TEXT,
                    timestamp TEXT
                )
            """)

            await db.commit()


    async def add_sensor(self, sensor) -> None:

        async with aiosqlite.connect(self.db_path) as db:

            await db.execute("""
                INSERT OR IGNORE INTO sensors(id, type)
                VALUES (?, ?)
            """, (
                sensor["id"],
                sensor["type"],
            ))

            await db.commit()


    async def remove_sensor(self, sensor_id: str) -> None:

        async with aiosqlite.connect(self.db_path) as db:

            await db.execute(
                "DELETE FROM sensors WHERE id = ?",
                (sensor_id,)
            )

            await db.commit()


    async def list_sensors(self):

        async with aiosqlite.connect(self.db_path) as db:

            cursor = await db.execute(
                "SELECT id, type FROM sensors"
            )

            rows = await cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "type": row[1],
                }
                for row in rows
            ]


    async def add_reading(self, reading) -> None:

        async with aiosqlite.connect(self.db_path) as db:

            await db.execute("""
                INSERT INTO readings (
                    sensor_id,
                    reading_type,
                    value,
                    unit,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                reading["sensor_id"],
                reading["reading_type"],
                reading["value"],
                reading["unit"],
                reading["timestamp"],
            ))

            await db.commit()


    async def get_readings(
        self,
        sensor_id: str,
        from_ts=None,
        to_ts=None,
    ):

        query = """
            SELECT
                sensor_id,
                reading_type,
                value,
                unit,
                timestamp
            FROM readings
            WHERE sensor_id = ?
        """

        params = [sensor_id]

        async with aiosqlite.connect(self.db_path) as db:

            cursor = await db.execute(query, params)

            rows = await cursor.fetchall()

            return [
                {
                    "sensor_id": row[0],
                    "reading_type": row[1],
                    "value": row[2],
                    "unit": row[3],
                    "timestamp": row[4],
                }
                for row in rows
            ]