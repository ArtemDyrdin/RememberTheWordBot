from app.db.connection import get_db
import datetime
from app.db.connection import get_db
from app.services.srs import SRSService
import logging

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
        
async def get_words_for_review(user_id: int) -> list[dict]:
    """
    Выбирает все слова пользователя, у которых время next_review меньше или равно текущему.
    Возвращает список слов вместе с их переводами и контекстом.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    query = """
    SELECT id, word, transcription, repeat_count, ease_factor 
    FROM words 
    WHERE user_id = ? AND next_review <= ?
    ORDER BY next_review ASC;
    """
    
    async with get_db() as db:
        async with db.execute(query, (user_id, now)) as cursor:
            rows = await cursor.fetchall()
            words_list = []
            
            for row in rows:
                word_id = row['id']
                
                # Достаем переводы для этого слова
                async with db.execute("SELECT translation FROM translations WHERE word_id = ?", (word_id,)) as t_cursor:
                    translations = [t['translation'] for t in await t_cursor.fetchall()]
                
                # Достаем контекст (может быть пустым)
                async with db.execute("SELECT context_text FROM contexts WHERE word_id = ? LIMIT 1", (word_id,)) as c_cursor:
                    context_row = await c_cursor.fetchone()
                    context = context_row['context_text'] if context_row else None
                
                words_list.append({
                    "id": word_id,
                    "word": row['word'],
                    "transcription": row['transcription'],
                    "repeat_count": row['repeat_count'],
                    "ease_factor": row['ease_factor'],
                    "translations": translations,
                    "context": context
                })
                
            return words_list

async def update_word_after_review(word_id: int, is_correct: bool) -> None:
    """
    Достает текущие метрики слова, пересчитывает их через SM-2,
    обновляет запись в БД и пишет лог в review_log.
    """
    async with get_db() as db:
        try:
            # 1. Получаем текущие данные слова и user_id
            async with db.execute(
                "SELECT user_id, repeat_count, ease_factor FROM words WHERE id = ?", 
                (word_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    logging.warning(f"Слово с ID {word_id} не найдено в базе при обновлении.")
                    return
                
                user_id = row['user_id']
                current_repeat_count = row['repeat_count']
                current_ease_factor = row['ease_factor']

            # 2. Считаем новые параметры через сервис алгоритма
            new_repeat, new_ease, next_review_dt = SRSService.calculate_next_review(
                current_repeat_count=current_repeat_count,
                current_ease_factor=current_ease_factor,
                is_correct=is_correct
            )
            
            next_review_str = next_review_dt.strftime("%Y-%m-%d %H:%M:%S")

            # 3. Обновляем таблицу words (строго нужные поля, не трогая word)
            update_query = """
            UPDATE words 
            SET repeat_count = ?, ease_factor = ?, next_review = ? 
            WHERE id = ?;
            """
            await db.execute(update_query, (new_repeat, new_ease, next_review_str, word_id))
            
            # 4. Пишем лог в review_log абсолютно изолированно
            log_query = """
            INSERT INTO review_log (word_id, user_id, quality, interval_days)
            VALUES (?, ?, ?, ?);
            """
            quality = 5 if is_correct else 1
            interval_days = int((next_review_dt - datetime.datetime.now()).days)
            if interval_days == 0:
                interval_days = 1  # Для шага 0.5 дня пишем 1 день в лог
                
            await db.execute(log_query, (word_id, user_id, quality, interval_days))
            
            logging.info(f"Слово ID {word_id} успешно обновлено. Новый интервал улетает на: {next_review_str}")

        except Exception as e:
            # Если что-то пойдет не так, откатываем всю транзакцию
            await db.rollback()
            raise e