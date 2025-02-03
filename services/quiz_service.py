# services/quiz_service.py

import asyncio
import random
import base64
import uuid
from datetime import datetime
from typing import List, Dict

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import db, bot, dp
from services.keyboard_service import KeyboardService
from states.room_states import QuizStates
from utils.logging_utils import logger

keyboard_service = KeyboardService()
# services/quiz_service.py
class QuizService:
    def __init__(self):
        self.db = db
        self.TIMEOUT = 30
        self.DEFAULT_QUESTIONS_COUNT = 30
        self.bot_username = None  # config dan olish kerak

    async def get_bot_username(self):
        if not self.bot_username:
            bot_user = await bot.get_me()
            self.bot_username = bot_user.username
        return self.bot_username

    async def generate_invite_link(self, user_id: int, quiz_id: int, unique_id: str,
                                   quiz_number: int, quiz_time: int, quiz_name: str) -> str:
        bot_username = await self.get_bot_username()
        return (f"https://t.me/{bot_username}?start="
                f"{user_id}_quiz_{quiz_id}_{unique_id}_number_{quiz_number}_time_{quiz_time}_name_{quiz_name}")

    def _generate_unique_id(self) -> str:
        uuid_val = uuid.uuid4()
        return base64.urlsafe_b64encode(uuid_val.bytes)[:4].decode('utf-8').replace('_', '-')

    async def create_quiz(self, quiz_id: int, quiz_number: int, quiz_time: int, user_id: int) -> str:
            unique_id = self._generate_unique_id()
            current_time = datetime.now().strftime('%m-%d-%Y %H:%M')
            quiz_name = f"Quiz_{random.randint(1000, 9999)}"  # Quiz nomi

            self.db.add_history_entry(
                user_id=user_id,
                quiz_id=quiz_id,
                unique_id=unique_id,
                quiz_number=quiz_number,
                quiz_time=quiz_time,
                created_at=current_time
            )
            return unique_id, quiz_name

    async def get_battle_name(self, battle_id: int) -> str:
        try:
            battle = self.db.get_battle_by_id(battle_id)
            return battle[1] if battle else "Nomsiz test"
        except Exception as e:
            logger.error(f"Error getting battle name: {e}")
            return "Nomsiz test"



    async def handle_test_selection(self, parent_id: int):
        categories = self.db.get_battle_by_parent_id(parent_id)
        if categories:
            return {'type': 'categories', 'data': categories}

        questions = self.get_questions_by_battle_id(parent_id)
        if questions:
            return {'type': 'questions', 'data': questions}

        return {'type': 'empty', 'data': None}

        # services/quiz_service.py davomi

    async def start_quiz_battle(self, message, state, questions: list):
        await state.update_data(
            questions=questions,
            current_index=0,
            answers=[],
            quiz_ended=False
        )
        await QuizStates.WAITING_ANSWER.set()
        await self.send_next_question(message, state)

    async def send_next_question(self, message, state):
        try:
            data = await state.get_data()
            questions = data['questions']
            current_index = data.get('current_index', 0)
            total_questions = data.get('total_questions', len(questions))
            used_questions = data.get('used_questions', [])

            if current_index < total_questions:
                question = questions[current_index]

                # Savolni qayta ishlatmaslik uchun tekshirish
                if question not in used_questions:
                    used_questions.append(question)
                    task_id = random.randint(1, 1_000_000)

                    await state.update_data(
                        current_index=current_index + 1,
                        correct_answer=question['question'],
                        answered=False,
                        task_id=task_id,
                        used_questions=used_questions
                    )

                    await message.answer(f"{current_index + 1}/{total_questions}\n{question['answer_a']}")

                    timeout_task = asyncio.create_task(self.check_timeout(message, state, task_id))
                    await state.update_data(timeout_task_id=id(timeout_task))
            else:
                await self.end_quiz(message, state)

        except Exception as e:
            logger.error(f"Error in send_next_question: {e}")

    async def check_timeout(self, message, state, task_id: int):
        await asyncio.sleep(self.TIMEOUT)
        try:
            data = await state.get_data()
            if not data.get('answered') and data.get('task_id') == task_id:
                await self.save_answer(state, False)
                await message.answer("Vaqt tugadi!")
                await self.send_next_question(message, state)
        except Exception as e:
            logger.error(f"Timeout check error: {e}")

        # services/quiz_service.py davomi

    async def save_answer(self, state, is_correct: bool):
        try:
            data = await state.get_data()
            answers = data.get('answers', [])
            answers.append(is_correct)
            await state.update_data(
                answers=answers,
                answered=True
            )
        except Exception as e:
            logger.error(f"Error saving answer: {e}")

    async def process_answer(self, user_answer: str, correct_answer: str) -> bool:
        return user_answer.strip().lower() == correct_answer.strip().lower()

    async def save_quiz_result(self, user_id: int, unique_id: str, true_answers: int, false_answers: int,
                               name: str) -> None:
        try:
            user = self.db.get_user_by_chat_id(user_id)
            if not user:
                logger.error(f"User not found for chat_id: {user_id}")
                return

            self.db.add_results_entry(
                chat_id=user_id,
                unique_id=unique_id,
                true_answers=true_answers,
                false_answers=false_answers,
                user_name=name
            )
            logger.info(f"Saved quiz result for user {user_id}: {true_answers} correct, {false_answers} wrong")

        except Exception as e:
            logger.error(f"Error saving quiz result: {e}")

    async def format_quiz_result(self, user_name: str, answers: list, quiz_name: str, battle_name: str) -> str:
        correct_count = sum(answers)
        total_count = len(answers)

        result_message = (
            f"📊 Test yakunlandi!\n\n"
            f"👤 Qatnashchi: {user_name}\n"
            f"🎯 Test: {battle_name} ({quiz_name})\n"
            f"✅ To'g'ri javoblar: {correct_count}\n"
            f"❌ Noto'g'ri javoblar: {total_count - correct_count}\n"
            f"📈 Natija: {correct_count}/{total_count}"
        )
        return result_message

    async def end_quiz(self, message, state):
        try:
            data = await state.get_data()
            answers = data.get('answers', [])
            user_name = data.get('name', 'Foydalanuvchi')
            unique_id = data.get('unique_id')
            owner_id = data.get('owner_id')
            quiz_name = data.get('quiz_name')
            battle = await self.get_battle_name(data['quiz_id'])

            correct_count = sum(answers)
            false_count = len(answers) - correct_count

            if unique_id:
                await self.save_quiz_result(
                    user_id=message.from_user.id,
                    unique_id=unique_id,
                    true_answers=correct_count,
                    false_answers=false_count,
                    name=user_name
                )

            result = await self.format_quiz_result(user_name, answers, quiz_name, battle)
            await bot.send_message(owner_id, result)


            await message.answer(
                "Test yakunlandi! ✅\n"
                "Natijangizni test adminidan olishingiz mumkin."
            )

            await state.finish()
        except Exception as e:
            logger.error(f"Error ending quiz: {e}")

    async def get_subcategories(self, parent_id: int) -> List[Dict]:

        try:
            subcategories = self.db.get_battle_by_parent_id(parent_id)
            return subcategories if subcategories else []
        except Exception as e:
            logger.error(f"Error getting subcategories: {e}")
            return []

    async def get_questions_by_battle_id(self, battle_id: int) -> List[Dict]:

        try:
            questions = self.db.get_questions_by_battle_id(battle_id)
            logger.info(f"Found {len(questions) if questions else 0} questions for battle_id: {battle_id}")
            return questions if questions else []
        except Exception as e:
            logger.error(f"Error getting questions by battle_id: {e}")
            return []

    async def add_quiz_participant(self, unique_id: str, user_id: int, user_name: str):
        self.db.add_quiz_participant(unique_id, user_id, user_name)

    async def get_quiz_participants(self, unique_id: str) -> List[Dict]:
        return self.db.get_quiz_participants(unique_id)

    async def get_quiz_questions(self, unique_id: str) -> List[Dict]:
        try:
            quiz_data = self.db.get_quiz_by_unique_id(unique_id)
            if not quiz_data:
                logger.error(f"Quiz not found for unique_id: {unique_id}")
                return []

            quiz_id = quiz_data[0]
            quiz_number = int(quiz_data[1])

            questions = self.db.get_questions_by_battle_id(quiz_id)
            if not questions:
                logger.error(f"No questions found for quiz_id: {quiz_id}")
                return []

            random.shuffle(questions)

            return questions[:quiz_number]

        except Exception as e:
            logger.error(f"Error getting quiz questions: {e}")
            return []

    async def start_quiz_for_user(self, user_id: int, questions: list):
        try:
            state = dp.get_current().current_state(user=user_id, chat=user_id)
            task_id = random.randint(1, 1_000_000)

            # Savollar sonini tekshirish
            total_questions = len(questions)
            if total_questions == 0:
                await bot.send_message(user_id, "Kechirasiz, savollar topilmadi")
                return

            # Bitta savol faqat bir marta ishlatilishi uchun
            used_questions = []

            await state.update_data({
                'questions': questions,
                'current_index': 0,
                'answers': [],
                'quiz_ended': False,
                'answered': False,
                'task_id': task_id,
                'test_started': True,
                'used_questions': used_questions,  # Ishlatilgan savollarni kuzatish uchun
                'total_questions': total_questions  # Umumiy savollar soni
            })

            await state.set_state(QuizStates.WAITING_ANSWER.state)

            # Birinchi savolni yuborish
            await self.send_next_question(
                types.Message(chat=types.Chat(id=user_id)),
                state
            )

        except Exception as e:
            logger.error(f"Error starting quiz for user {user_id}: {e}")


    async def get_quiz_by_unique_id(self, unique_id: str) -> Dict:
        """Quiz ma'lumotlarini olish"""
        quiz = self.db.get_quiz_by_unique_id(unique_id)
        if quiz:
            return {
                'quiz_id': quiz[0],
                'quiz_number': quiz[1],
                'quiz_time': quiz[2],
                'unique_id': quiz[3],
                'user_id': quiz[4],
                'created_at': quiz[5]
            }
        return None