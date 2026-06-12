from app.db.connection import get_db
import datetime

async def save_new_word(
    user_id: int, 
    word: str, 
    transcription: str | None, 
    translations: list[str], 
    context: str | None
) -> int | None:
    """
    Сохраняет новое слово, его переводы и контекст в базу данных.
    Возвращает ID созданного слова.
    """
    # По умолчанию для SM-2 ставим next_review на текущий момент, 
    # чтобы слово сразу было доступно для первого повторения
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    query_word = """
    INSERT INTO words (user_id, word, transcription, next_review)
    VALUES (?, ?, ?, ?);
    """
    
    query_translation = """
    INSERT INTO translations (word_id, translation, sort_order)
    VALUES (?, ?, ?);
    """
    
    query_context = """
    INSERT INTO contexts (word_id, context_text)
    VALUES (?, ?);
    """

    async with get_db() as db:
        try:
            # 1. Сохраняем само слово
            cursor = await db.execute(query_word, (user_id, word, transcription, now))
            word_id = cursor.lastrowid
            
            if not word_id:
                return None

            # 2. Сохраняем все переводы из массива чипсов
            for index, trans in enumerate(translations):
                await db.execute(query_translation, (word_id, trans.strip(), index))

            # 3. Сохраняем контекст (если пользователь его оставил)
            if context and context.strip():
                await db.execute(query_context, (word_id, context.strip()))

            # Так как мы выходим из контекстного менеджера get_db без ошибок,
            # aiosqlite автоматически сделает await db.commit()
            return word_id

        except Exception as e:
            # В случае любой ошибки транзакция откатится, если мы вызовем rollback явным образом
            await db.rollback()
            raise e