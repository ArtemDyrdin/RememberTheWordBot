import aiosqlite
from app.config import settings

SQL_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    lang_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    transcription TEXT,
    repeat_count INTEGER DEFAULT 0,
    ease_factor REAL DEFAULT 2.5,
    next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (tg_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    translation TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    context_text TEXT NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    quality INTEGER NOT NULL,
    interval_days INTEGER NOT NULL,
    reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (tg_id) ON DELETE CASCADE
);
"""

async def init_database():
    async with aiosqlite.connect('local.db') as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.executescript(SQL_CREATE_TABLES)
        await db.commit()