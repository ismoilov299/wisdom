# utils/validators.py
from constants.quiz_constants import MAX_QUIZ_NUMBER, MIN_QUIZ_TIME, MAX_QUIZ_TIME
from utils.logging_utils import logger


class QuizValidator:
    @staticmethod
    def validate_quiz_number(number: str) -> bool:
        try:
            num = int(number)
            return 0 < num <= MAX_QUIZ_NUMBER
        except ValueError:
            return False

    @staticmethod
    def validate_quiz_time(time: str) -> bool:
        try:
            time_val = int(time)
            return MIN_QUIZ_TIME <= time_val <= MAX_QUIZ_TIME
        except ValueError:
            return False

# utils/message_utils.py
from typing import Optional
from aiogram import types
from aiogram.utils.exceptions import RetryAfter
import asyncio

async def safe_send_message(message: types.Message, text: str,
                          reply_markup: Optional[types.InlineKeyboardMarkup] = None,
                          retry_count: int = 3) -> Optional[types.Message]:
    for attempt in range(retry_count):
        try:
            return await message.answer(text, reply_markup=reply_markup)
        except RetryAfter as e:
            await asyncio.sleep(e.timeout + 1)
        except Exception as e:
            logger.error(f"Message sending error: {e}")
            return None