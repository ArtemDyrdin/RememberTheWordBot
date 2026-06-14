import json
import logging
import urllib.parse
import time
from aiogram import Router, F, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command

from app.db.words import get_words_for_review, update_word_after_review
from app.handlers.start import get_main_menu_keyboard

review_router = Router()

REVIEW_WEBAPP_URL = "https://artemdyrdin.github.io/RememberTheWordBot/review.html"

@review_router.message(F.text == "🧠 Повторить слова")
async def menu_review_words(message: Message) -> None:
    user_id = message.from_user.id
    words_to_review = await get_words_for_review(user_id)
    
    if not words_to_review:
        await message.answer(
            f"🎉 {html.bold('Великолепно!')} На данный момент у тебя нет слов для повторения.\n"
            f"Все карточки распределены по интервалам. Отдыхай!", 
            reply_markup=get_main_menu_keyboard()
        )
        return

    try:
        json_data = json.dumps(words_to_review, ensure_ascii=False)
        encoded_data = urllib.parse.quote(json_data)
        url_with_data = f"{REVIEW_WEBAPP_URL}?data={encoded_data}"

        inline_like_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🧠 Запустить сессию повторения", web_app=WebAppInfo(url=url_with_data))]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            f"📦 Карточек к повторению: {html.bold(len(words_to_review))}\n"
            f"Нажми кнопку ниже для старта сессии:", 
            reply_markup=inline_like_keyboard
        )
    except Exception as e:
        await message.answer("❌ Произошла ошибка при генерации сессии.")

@review_router.message(F.web_app_data, lambda msg: json.loads(msg.web_app_data.data).get("action") == "review")
async def handle_review_results(message: Message) -> None:
    logging.info(f"Получены данные из Web App Повторений: {message.web_app_data.data}")
    raw_data = message.web_app_data.data
    
    try:
        results = json.loads(raw_data)
        
        if not results:
            await message.answer("Сессия повторения была закрыта без ответов.", reply_markup=get_main_menu_keyboard())
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
        
        await message.answer(summary_text, reply_markup=get_main_menu_keyboard())

    except Exception as e:
        logging.error(f"Error while processing review results: {e}")
        await message.answer("❌ Не удалось сохранить прогресс повторения.", reply_markup=get_main_menu_keyboard())