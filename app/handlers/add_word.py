import json
import logging
from aiogram import Router, F, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

from app.db.words import save_new_word
from app.handlers.start import get_main_menu_keyboard

# Создаем роутер для добавления слов
add_word_router = Router()

# Ссылка на  развернутый Web App. 
WEBAPP_URL = "https://artemdyrdin.github.io/RememberTheWordBot/add_word.html" 

@add_word_router.message(F.text == "➕ Добавить слово")
async def menu_add_word(message: Message) -> None:
    """
    Генерирует свежую ссылку под Web App и выдает ОДНУ кнопку для открытия формы.
    """    
    inline_like_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Открыть форму добавления", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Нажми кнопку ниже, чтобы открыть карточку:", reply_markup=inline_like_keyboard)


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

        if word_id == None:
            await message.answer(f"❌ Ошибка при сохранении слова в базу данных.")
        elif word_id == -1:
            await message.answer(f"⚠️ {html.bold(word)} уже есть в твоем словаре.\n")
        else:
            # Красиво форматируем ответное сообщение в чате
            translations_str = ", ".join(translations)
            success_text = (
                f"✅ {html.bold('Слово успешно сохранено!')}\n\n"
                f"🇬🇧 {html.code(word)} {f'[{transcription}]' if transcription else ''}\n"
                f"🇷🇺 {translations_str}\n"
            )
            if context:
                success_text += f"📝 {html.italic('Контекст:')} {context}"
                
            await message.answer(success_text, reply_markup=get_main_menu_keyboard())

    except json.JSONDecodeError:
        logging.error(f"Failed to decode Web App JSON: {raw_data}")
        await message.answer("❌ Произошла ошибка при обработке данных из формы.")
    except Exception as e:
        logging.error(f"Error while saving Web App data: {e}")
        await message.answer("❌ Не удалось сохранить слово. Что-то пошло не так.")