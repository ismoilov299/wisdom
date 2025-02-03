#/category.py
from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.users.texts import TEXT_ALL
from services.keyboard_service import KeyboardService
from services.category_service import CategoryService
from loader import dp
from utils.logging_utils import logger

keyboard_service = KeyboardService()
category_service = CategoryService()
BOOKS_TEXT = ['📚 Kitoblar', '📚Книги']
BATTLE_TEXT = ['⚔️ Bellashuv', '⚔️ Соревнование']

@dp.message_handler(text=BOOKS_TEXT)
async def handle_product_request(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang_id = await category_service.get_user_language(user_id)
    categories = await category_service.get_root_categories()

    keyboard = await keyboard_service.create_keyboard(categories, lang_id, "category")
    await message.answer(text=TEXT_ALL[lang_id], reply_markup=keyboard)


@dp.message_handler(text=BATTLE_TEXT)
async def handle_battle_request(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        lang_id = await category_service.get_user_language(user_id)
        battles = await category_service.get_root_battles()

        # Admin ekanligini tekshirish
        is_admin = await category_service.is_admin(user_id)
        logger.info(f"User {user_id} is admin: {is_admin}")

        keyboard = await keyboard_service.create_keyboard(
            battles,
            lang_id,
            "battle",
            is_admin=is_admin  # Admin parametrini uzatamiz
        )
        await message.answer(text=TEXT_ALL[lang_id], reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Battle request error: {e}")