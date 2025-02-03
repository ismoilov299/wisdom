# services/keyboard_service.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.users.texts import BACK


class KeyboardService:
    @staticmethod
    async def create_keyboard(items: list, lang_id: int, keyboard_type: str = "category", is_admin: bool = False) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup()

        for item in items:
            item_id = item[0]
            name = item[1] if lang_id == 1 else item[2]

            if keyboard_type == "category":
                callback_data = f"category_{item_id}"
            elif keyboard_type == "battle":
                callback_data = f"battle_{item_id}_{name}"
            elif keyboard_type == "subcategory":
                callback_data = f"test_{item_id}_{name[:20]}"

            keyboard.add(InlineKeyboardButton(text=name, callback_data=callback_data))

        # Admin tugmasi
        if is_admin and keyboard_type == "battle":
            keyboard.add(InlineKeyboardButton(
                text="Test o'tkazish" if lang_id == 1 else "Пройти тест",
                callback_data="start_quiz"
            ))

        keyboard.add(InlineKeyboardButton(text=BACK[lang_id], callback_data="back_to_battle"))
        return keyboard

    @staticmethod
    async def create_quiz_result_keyboard(unique_id: str) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Reytingni olish", callback_data=f"get_rating_{unique_id}"))
        return keyboard

    @staticmethod
    async def create_admin_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup()
        if is_admin:
            keyboard.add(InlineKeyboardButton("Test o'tkazish", callback_data="start_quiz"))
        return keyboard