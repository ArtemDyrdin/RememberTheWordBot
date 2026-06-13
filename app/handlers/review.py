import json
import logging
import urllib.parse
import time
from aiogram import Router, F, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command

from app.db.words import get_words_for_review, update_word_after_review

review_router = Router()

REVIEW_WEBAPP_URL = "https://artemdyrdin.github.io/RememberTheWordBot/review.html"

@review_router.message(Command("review"))
async def command_review_words(message: Message) -> None:
    """
    Хэндлер команды /review. Собирает слова для повторения,
    упаковывает их в URL и выкатывает кнопку Web App.
    """
    user_id = message.from_user.id
    
    # 1. Получаем список слов из БД, у которых next_review <= текущему времени
    words_to_review = await get_words_for_review(user_id)
    
    if not words_to_review:
        await message.answer(
            f"🎉 {html.bold('Great!')} На данный момент у тебя нет слов для повторения.\n"
            f"Все карточки распределены по интервалам. Отдыхай или добавь новые слова через /add!"
        )
        return

    try:
        # 2. Сериализуем данные в JSON-строку
        json_data = json.dumps(words_to_review, ensure_ascii=False)
        
        # 3. Кодируем строку для безопасной передачи в параметрах URL
        encoded_data = urllib.parse.quote(json_data)
        
        # Добавляем cache-busting флаг версии (timestamp), чтобы избежать жесткого кэша ТГ
        version_flag = int(time.time())
        full_url = f"{REVIEW_WEBAPP_URL}?data={encoded_data}&v={version_flag}"
        
        # 4. Создаем Reply-клавиатуру с кнопкой Web App
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="🧠 Начать повторение слов",
                        web_app=WebAppInfo(url=full_url)
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            f"📦 Количество слов к повторению сегодня: {html.bold(len(words_to_review))}\n\n"
            f"Нажми на кнопку ниже, чтобы запустить интерактивную сессию повторения:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logging.error(f"Error encoding words for review: {e}")
        await message.answer("❌ Произошла ошибка при генерации сессии повторения.")


@review_router.message(F.web_app_data, lambda msg: json.loads(msg.web_app_data.data).get("action") == "review")
async def handle_review_results(message: Message) -> None:
    logging.info(f"Получены данные из Web App Повторений: {message.web_app_data.data}")
    raw_data = message.web_app_data.data
    
    try:
        results = json.loads(raw_data)
        
        if not results:
            await message.answer("Сессия повторения была закрыта без ответов.")
            return

        correct_count = 0
        actual_words_count = 0

        # Перебираем результаты
        for word_id_str, is_correct in results.items():
            # Если наткнулись на служебный маркер, просто пропускаем его
            if word_id_str == "action":
                continue
                
            word_id = int(word_id_str)
            actual_words_count += 1
            
            # Обновляем в БД
            await update_word_after_review(word_id=word_id, is_correct=is_correct)
            
            if is_correct:
                correct_count += 1

        # Формируем итоговую статистику
        wrong_count = actual_words_count - correct_count
        summary_text = (
            f"🏁 {html.bold('Сессия повторения успешно завершена!')}\n\n"
            f"📊 {html.bold('Твои результаты:')}\n"
            f"✅ Правильно: {html.underline(correct_count)}\n"
            f"❌ Ошибок: {html.underline(wrong_count)}\n\n"
            f"Интервалы повторения обновлены!"
        )
        
        await message.answer(summary_text)

    except Exception as e:
        logging.error(f"Error while processing review results: {e}")
        await message.answer("❌ Не удалось сохранить прогресс повторения.")