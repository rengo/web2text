import asyncpg
import json
import logging
import asyncio
import uuid
from datetime import datetime, date
from shared.core.database import DATABASE_URL

logger = logging.getLogger("worker.notifications")

class RemoteLogger:
    def __init__(self):
        self.conn = None

    async def initialize(self):
        try:
            # asyncpg expects 'postgresql://' not 'postgresql+asyncpg://'
            dsn = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            self.conn = await asyncpg.connect(dsn)
            logger.info("Connected to Postgres for notifications")
        except Exception as e:
            logger.error(f"Failed to connect to Postgres for notifications: {e}")

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def log(self, message: str, level: str = "info", extra: dict = None):
        if not self.conn:
            return
            
        payload = {
            "message": message,
            "level": level,
            "extra": extra or {}
        }
        # Helper to serialize UUIDs/dates
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, uuid.UUID):
                return str(obj)
            return str(obj)

        try:
            await self.conn.execute(f"NOTIFY worker_logs, '{json.dumps(payload, default=json_serial)}'")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            # Try to reconnect if closed
            if self.conn and self.conn.is_closed():
                await self.initialize()

remote_logger = RemoteLogger()
