import os
from contextlib import asynccontextmanager
import aiosqlite

DB_PATH = "local.db"

@asynccontextmanager
async def get_db():
    """
    Асинхронный контекстный менеджер для работы с БД.
    Автоматически закрывает соединение и делает commit при выходе.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        db.row_factory = aiosqlite.Row
        
        yield db
        await db.commit()