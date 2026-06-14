from aiogram import Router, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from app.db.users import register_user

core_router = Router()

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает постоянное главное меню бота без привязки WebApp (просто текст).
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить слово"),
                KeyboardButton(text="🧠 Повторить слова")
            ],
            [
                KeyboardButton(text="📊 Статистика")  # Задел на будущее
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

@core_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Хэндлер на команду /start. Регистрирует юзера и отправляет приветствие.
    """
    user = message.from_user
    if not user:
        return

    # Вызываем асинхронную регистрацию в БД
    is_new_user = await register_user(
        tg_id=user.id,
        username=user.username,
        first_name=user.first_name,
        lang_code=user.language_code
    )

    if is_new_user:
        welcome_text = (
            f"Привет, {html.bold(user.first_name)}! 👋\n\n"
            f"Я сохранил тебя в базу данных. Теперь ты можешь добавлять "
            f"английские слова и повторять их по системе интервальных повторений!"
        )
    else:
        welcome_text = f"С возвращением, {html.bold(user.first_name)}! Рад снова тебя видеть. Раунд повторения слов?"

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        )