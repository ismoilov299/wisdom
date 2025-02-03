# services/question_service.py
from typing import Dict, Optional
import asyncio
import random

from utils.logging_utils import logger


class QuestionService:
    TIMEOUT_DURATION = 30

    @staticmethod
    async def check_answer(user_answer: str, true_answer: str) -> bool:
        return user_answer.strip().lower() == true_answer.strip().lower()

    @staticmethod
    async def format_quiz_result(answers: list, name: str) -> str:
        correct_count = sum(answers)
        result = "\n".join(f"{i + 1}. {'✅' if ans else '❌'}" for i, ans in enumerate(answers))
        return f"{name} ning natijalari:\n{result}\n\n{correct_count}/{len(answers)} to'g'ri javob"

    async def start_timeout_check(self, message, state, task_id: int):
        await asyncio.sleep(self.TIMEOUT_DURATION)
        try:
            data = await state.get_data()
            if data.get('answered') or data.get('current_task_id') != task_id:
                return

            if data.get('quiz_ended'):
                return

            answers = data.get('answers_list', [])
            answers.append(False)
            await state.update_data(answers_list=answers)
            await message.answer("Vaqt tugadi!")

        except Exception as e:
            logger.error(f"Timeout check error: {e}")



