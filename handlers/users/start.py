# handlers/start.py
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from services.user_service import UserService
from services.auth_service import AuthService
from services.menu_service import MenuService

from constants.error_messages import ERRORS
from handlers.users.texts import TEXT_MAIN_MENU
from loader import dp,db
from utils.logging_utils import logger

user_service = UserService(db)
auth_service = AuthService(db)
menu_service = MenuService(db)


@dp.message_handler(CommandStart(), state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        start_args = message.get_args()

        if start_args:
            return await auth_service.process_deep_link(message, state, start_args)

        user = await user_service.get_or_create_user(user_id)
        if not user:
            return await auth_service.start_registration(message, state)

        lang_id = await user_service.get_user_language(user_id)
        keyboard = await menu_service.get_main_menu(user_id)
        print("ishladi")
        await message.answer(TEXT_MAIN_MENU[lang_id], reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Start command error: {e}")
