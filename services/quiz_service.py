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
        self.bot_username = None
        # Cache for active quizzes
        self._active_quizzes = {}
        # Cache for questions
        self._questions_cache = {}
        # Cache timeout (1 hour)
        self.CACHE_TIMEOUT = 3600
        self._active_quizzes = {}

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

    async def _get_question(self, question_data: dict) -> dict:
        """
        Savolni cache dan yoki bazadan olish
        """
        try:
            question_id = question_data.get('id')

            # Cache dan tekshirish
            if question_id in self._questions_cache:
                return self._questions_cache[question_id]

            # Cache da bo'lmasa, original savolni qaytarish
            self._questions_cache[question_id] = question_data
            return question_data

        except Exception as e:
            logger.error(f"Error getting question: {e}")
            return question_data

    async def get_active_quiz(self, unique_id: str) -> dict:
        return self._active_quizzes.get(unique_id)

    async def set_quiz_started(self, unique_id: str):
        self._active_quizzes[unique_id] = {
            'started': True,
            'start_time': datetime.now()
        }

    # quiz_service.py
    async def create_quiz(self, quiz_id: int, quiz_number: int, quiz_time: int, user_id: int) -> str:
        try:
            unique_id = self._generate_unique_id()
            current_time = datetime.now().strftime('%m-%d-%Y %H:%M')
            quiz_name = f"Quiz_{random.randint(1000, 9999)}"

            # Barcha kerakli argumentlar bilan funksiyani chaqirish
            self.db.add_history_entry(
                user_id=user_id,  # Foydalanuvchi ID
                quiz_id=quiz_id,  # Test ID
                unique_id=unique_id,  # Unikal ID
                quiz_number=quiz_number,  # Savollar soni
                quiz_time=quiz_time,  # Test vaqti
                created_at=current_time  # Yaratilgan vaqti
            )

            return unique_id, quiz_name

        except Exception as e:
            logger.error(f"Error creating quiz: {e}")
            raise

            # self.db.add_history_entry(
            #     user_id=user_id,
            #     quiz_id=quiz_id,
            #     unique_id=unique_id,
            #     quiz_number=quiz_number,
            #     quiz_time=quiz_time,
            #     created_at=current_time
            # )
            # return unique_id, quiz_name

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

            # Test boshlanmaganligini tekshirish
            if not data.get('test_started'):
                return

            questions = data['questions']
            current_index = data.get('current_index', 0)
            total_questions = data.get('total_questions', len(questions))
            quiz_time = data.get('quiz_time', self.TIMEOUT)

            # Test tugagan bo'lsa
            if current_index >= total_questions:
                return await self.end_quiz(message, state)

            # Joriy savolni olish
            question = questions[current_index]

            # State ni yangilash
            new_task_id = random.randint(1, 1_000_000)
            await state.update_data({
                'current_index': current_index + 1,
                'correct_answer': question['question'],
                'answered': False,
                'task_id': new_task_id,
                'current_task_completed': False
            })

            # Savolni yuborish
            await message.answer(
                f"{current_index + 1}/{total_questions}\n{question['answer_a']}"
            )

            # Yangi timeout task yaratish
            asyncio.create_task(
                self.check_timeout(message, state, new_task_id)
            )

        except Exception as e:
            logger.error(f"Error in send_next_question: {e}")

    async def check_timeout(self, message, state, task_id: int):
        try:
            data = await state.get_data()
            quiz_time = data.get('quiz_time', self.TIMEOUT)  # Test vaqtini olish

            await asyncio.sleep(quiz_time)  # Berilgan vaqt kutish

            current_data = await state.get_data()
            current_task_id = current_data.get('task_id')

            # Vaqt tugagan va javob berilmagan bo'lsagina
            if not current_data.get('answered') and current_task_id == task_id:
                await message.answer("Vaqt tugadi!")
                await self.save_answer(state, False)  # Noto'g'ri javob sifatida saqlash
                # Keyingi savolga o'tish
                await self.send_next_question(message, state)

        except Exception as e:
            logger.error(f"Timeout check error: {e}")

        # services/quiz_service.py davomi

    async def save_answer(self, state, is_correct: bool):
        try:
            data = await state.get_data()
            answers = data.get('answers', [])
            answers.append(is_correct)

            # Javob berilganini belgilash
            await state.update_data({
                'answers': answers,
                'answered': True,
                'current_task_completed': True
            })
        except Exception as e:
            logger.error(f"Error saving answer: {e}")

    async def process_answer(self, user_answer: str, correct_answer: str) -> bool:
        try:
            # Javobni tekshirish
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            return is_correct
        except Exception as e:
            logger.error(f"Error processing answer: {e}")
            return False

    async def _bulk_save_results(self):
        try:
            if not hasattr(self, '_results_cache'):
                return

            if not self._results_cache:
                return

            for result in self._results_cache:
                self.db.add_results_entry(
                    chat_id=result['chat_id'],
                    unique_id=result['unique_id'],
                    true_answers=result['true_answers'],
                    false_answers=result['false_answers'],
                    user_name=result['user_name']
                )

            self._results_cache = []

        except Exception as e:
            logger.error(f"Error in bulk saving results: {e}")

    async def save_quiz_result(self, user_id: int, unique_id: str, true_answers: int,
                               false_answers: int, name: str) -> None:
        try:
            # Batch save results
            results_data = {
                'chat_id': user_id,
                'unique_id': unique_id,
                'true_answers': true_answers,
                'false_answers': false_answers,
                'user_name': name,
                'timestamp': datetime.now()
            }

            # Cache results before saving to DB
            if not hasattr(self, '_results_cache'):
                self._results_cache = []

            self._results_cache.append(results_data)

            # Batch save if cache reaches limit
            if len(self._results_cache) >= 10:
                await self._bulk_save_results()

        except Exception as e:
            logger.error(f"Error saving quiz result: {e}")

    async def format_quiz_result(self, user_name: str, quiz_name: str, battle_name: str) -> tuple:
        """Test natijasi uchun xabar va keyboard yaratish"""
        message = (
            f"📊 Test yakunlandi!\n\n"
            f"👤 Qatnashchi: {user_name}\n"
            f"🎯 Test: {battle_name} ({quiz_name})"
        )

        # Inline tugmalarni yaratish
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton(
                "Alohida natija",
                callback_data=f"personal_result_{user_name}"
            ),
            types.InlineKeyboardButton(
                "Umumiy natija",
                callback_data="group_results"
            )
        )

        return message, keyboard

    async def get_detailed_results(self, user_name: str, answers: list, questions: list) -> str:
        try:
            total_questions = len(questions)
            if total_questions == 0:
                return "Natijalar topilmadi"

            correct_answers = sum(1 for a in answers if a)  # True qiymatlar soni
            percentage = round((correct_answers / total_questions) * 100, 1) if total_questions > 0 else 0

            result = [
                f"👤 {user_name} ning batafsil natijalari:\n",
                f"📈 Umumiy natija: {percentage}%\n",
                "\nSavollar tahlili:"
            ]

            for i, (question, is_correct) in enumerate(zip(questions, answers), 1):
                status = "✅" if is_correct else "❌"
                result.append(
                    f"\n{i}. {status} Savol: {question['answer_a']}\n"
                    f"   To'g'ri javob: {question['question']}"
                )

            return "\n".join(result)
        except Exception as e:
            logger.error(f"Error in get_detailed_results: {e}")
            return "Natijalarni ko'rsatishda xatolik yuz berdi"

    async def get_group_results(self, unique_id: str) -> str:
        participants = self.db.get_quiz_results(unique_id)
        if not participants:
            return "Bu test uchun natijalar topilmadi"

        results = []
        for p in participants:
            total = p['true_answers'] + p['false_answers']
            percentage = round((p['true_answers'] / total) * 100, 1) if total > 0 else 0
            results.append({
                'name': p['user_name'],
                'percentage': percentage,
                'correct': p['true_answers'],
                'total': total
            })

        results.sort(key=lambda x: x['percentage'], reverse=True)

        message = ["📊 Test natijalari (reyting):\n"]
        for i, r in enumerate(results, 1):
            message.append(
                f"{i}. {r['name']}: {r['percentage']}% "
                f"({r['correct']}/{r['total']})"
            )

        return "\n".join(message)

    async def end_quiz(self, message, state):
        try:
            data = await state.get_data()
            user_name = data.get('name', 'Foydalanuvchi')
            unique_id = data.get('unique_id')
            owner_id = data.get('owner_id')
            quiz_name = data.get('quiz_name')
            battle = await self.get_battle_name(data['quiz_id'])
            answers = data.get('answers', [])

            if unique_id:
                # Natijalarni saqlash
                await self.save_quiz_result(
                    user_id=message.from_user.id,
                    unique_id=unique_id,
                    true_answers=sum(1 for a in answers if a),
                    false_answers=sum(1 for a in answers if not a),
                    name=user_name
                )

            # Natija xabari va keyboard yaratish
            result_message, keyboard = await self.format_quiz_result(
                user_name, quiz_name, battle
            )

            # Natijani faqat adminga yuborish
            if owner_id:
                await bot.send_message(owner_id, result_message, reply_markup=keyboard)

            # Foydalanuvchiga oddiy xabar
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
            current_state = await state.get_state()

            if current_state == QuizStates.WAITING_ANSWER.state:
                return

            # Questions ni random qilish
            shuffled_questions = random.sample(questions, len(questions))

            # Initialize quiz data in one operation
            quiz_data = {
                'questions': shuffled_questions,
                'current_index': 0,
                'answers': [],
                'test_started': True,
                'total_questions': len(shuffled_questions),
                'start_time': datetime.now().timestamp(),
                'task_id': random.randint(1, 1_000_000)  # Unique task ID
            }

            await state.set_state(QuizStates.WAITING_ANSWER.state)
            await state.update_data(quiz_data)

            message = types.Message(chat=types.Chat(id=user_id))
            await self.send_next_question(message, state)

        except Exception as e:
            logger.error(f"Error starting quiz for user {user_id}: {e}")

    async def validate_quiz_session(self, unique_id: str, user_id: int) -> bool:
        """Validate quiz session and permissions"""
        if unique_id not in self._active_quizzes:
            return False

        quiz = self._active_quizzes[unique_id]
        # Check if quiz is still active
        if (datetime.now() - quiz['start_time']).seconds > self.CACHE_TIMEOUT:
            await self._cleanup_quiz(unique_id)
            return False

        return True




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