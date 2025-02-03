# services/user_service.py
from aiogram import types

from handlers.users.texts import BTN_BOOK, BTN_BATTLE, BTN_INFO, BTN_SETTINGS, BTN_ABOUT_US


class UserService:
    def __init__(self, db):
        self.db = db

    async def get_or_create_user(self, user_id: int):
        user = self.db.get_user_by_chat_id(user_id)
        if not user:
            self.db.add_user(chat_id=user_id)
        return user

    async def get_user_language(self, user_id: int) -> int:
        return self.db.get_user_language_id(user_id)


# services/menu_service.py

