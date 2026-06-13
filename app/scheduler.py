import logging
import datetime
from aiogram import Bot, html
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.words import get_all_users_expired_words_count

async def check_and_notify_users(bot: Bot) -> None:
    """
    Проверяет базу на наличие просроченных слов и рассылает пуши.
    Не отправляет уведомления в ночное время (с 23:00 до 07:00).
    """
    # 1. Проверяем текущий час сервера
    current_hour = datetime.datetime.now().hour
    
    # Если время от 23 ночи (включительно) до 7 утра (не включая 7:00, т.е. 00:00-06:59)
    if current_hour >= 23 or current_hour < 7:
        logging.info(f"Фоновая проверка пропущена (ночной режим, текущий час: {current_hour})")
        return

    logging.info("Запуск фоновой проверки интервальных повторений...")
    try:
        user_words_map = await get_all_users_expired_words_count()
        
        for tg_id, count in user_words_map.items():
            if count > 0:
                try:
                    await bot.send_message(
                        chat_id=tg_id,
                        text=(
                            f"🧠 {html.bold('Пора повторить слова!')}\n\n"
                            f"В твоем словаре накопилось {html.underline(count)} карточек, "
                            f"готовых к проверке.\n"
                            f"Используй команду /review, чтобы запустить сессию."
                        )
                    )
                    logging.info(f"Уведомление о повторении отправлено пользователю {tg_id}")
                except Exception as send_error:
                    logging.warning(f"Не удалось отправить пуш пользователю {tg_id}: {send_error}")
                    
    except Exception as e:
        logging.error(f"Ошибка в таске планировщика: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Инициализирует и запускает APScheduler
    """
    scheduler = AsyncIOScheduler()
    
    # Проверка крутится раз в час круглые сутки, но логика внутри сама спит ночью
    scheduler.add_job(
        check_and_notify_users,
        trigger="interval",
        hours=1,
        args=[bot],
        id="srs_reminder_job",
        replace_existing=True
    )
    
    return scheduler