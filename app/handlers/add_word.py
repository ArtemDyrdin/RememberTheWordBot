import json
import logging
from aiogram import Router, F, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import Command

from app.db.words import save_new_word

# Создаем роутер для добавления слов
add_word_router = Router()

# Ссылка на  развернутый Web App. 
WEBAPP_URL = "https://artemdyrdin.github.io/RememberTheWordBot/add_word.html" 

@add_word_router.message(Command("add"))
async def command_add_word(message: Message) -> None:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить слово", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "Нажмите на кнопку ниже для добавления нового слова:",
        reply_markup=keyboard
    )


@add_word_router.message(F.web_app_data, lambda msg: json.loads(msg.web_app_data.data).get("action") == "add")
async def handle_web_app_data(message: Message) -> None:
    """
    Ловит данные, отправленные из Mini App через Telegram.WebApp.sendData()
    """
    user_id = message.from_user.id
    logging.info(f"Получены данные из Web App: {message.web_app_data.data}")
    raw_data = message.web_app_data.data
    
    try:
        # Парсим JSON, прилетевший от фронтенда
        payload = json.loads(raw_data)
        
        word = payload.get("word")
        transcription = payload.get("transcription")
        translations = payload.get("translations", [])
        context = payload.get("context")

        # Сохраняем в базу данных SQLite
        word_id = await save_new_word(
            user_id=user_id,
            word=word,
            transcription=transcription,
            translations=translations,
            context=context
        )

        if word_id:
            # Красиво форматируем ответное сообщение в чате
            translations_str = ", ".join(translations)
            success_text = (
                f"✅ {html.bold('Слово успешно сохранено!')}\n\n"
                f"🇬🇧 {html.code(word)} {f'[{transcription}]' if transcription else ''}\n"
                f"🇷🇺 {translations_str}\n"
            )
            if context:
                success_text += f"📝 {html.italic('Контекст:')} {context}"
                
            await message.answer(success_text)
        else:
            await message.answer("❌ Ошибка при сохранении слова в базу данных.")

    except json.JSONDecodeError:
        logging.error(f"Failed to decode Web App JSON: {raw_data}")
        await message.answer("❌ Произошла ошибка при обработке данных из формы.")
    except Exception as e:
        logging.error(f"Error while saving Web App data: {e}")
        await message.answer("❌ Не удалось сохранить слово. Что-то пошло не так.")