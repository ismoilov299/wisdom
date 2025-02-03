# Room bilan ishlash uchun service
# services/room_service.py
from datetime import datetime
from typing import Dict, List

from aiogram import types


class RoomService:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def generate_invite_link(self, user_id: int, quiz_id: int,
                                 quiz_number: int, quiz_time: int, bot_username: str) -> str:
        unique_id = await self.quiz_service.create_quiz(quiz_id, quiz_number, quiz_time, user_id)
        return f"https://t.me/{bot_username}?start={user_id}_quiz_{quiz_id}_{unique_id}_number_{quiz_number}_time_{quiz_time}"

    async def broadcast_result(self, user_id: int, result_message: str,
                             unique_id: str, keyboard: types.InlineKeyboardMarkup):
        await self.bot.send_message(
            chat_id=user_id,
            text=result_message,
            reply_markup=keyboard
        )