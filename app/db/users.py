from app.db.connection import get_db

async def register_user(tg_id: int, username: str | None, first_name: str, lang_code: str | None) -> bool:
    """
    Регистрирует пользователя в базе данных, если его там еще нет.
    Возвращает True, если пользователь новый и был успешно добавлен.
    """
    query = """
    INSERT OR IGNORE INTO users (tg_id, username, first_name, lang_code)
    VALUES (?, ?, ?, ?);
    """
    async with get_db() as db:
        cursor = await db.execute(query, (tg_id, username, first_name, lang_code))
        return cursor.rowcount > 0