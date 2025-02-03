# handlers/quiz.py
from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.users.texts import TEXT_QUIZ
from keyboards.inline.room import end_quiz
from loader import dp
from services.quiz_service import QuizService
from states.room_states import RoomQuizStates, GroupQuizStates, QuizStates
from utils.logging_utils import logger

from services.category_service import CategoryService
from services.keyboard_service import KeyboardService

category_service = CategoryService()
keyboard_service = KeyboardService()


quiz_service = QuizService()


async def send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('questions', [])
    current_index = data.get('current_index', 0)

    if current_index < len(questions):
        question = questions[current_index]
        await state.update_data(
            current_index=current_index + 1,
            current_question=question
        )
        await message.answer(f"{current_index + 1}/{len(questions)}\n{question['answer_a']}")
    else:
        await end_quiz(message, state)


@dp.callback_query_handler(text="start_quiz")
async def start_quiz(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_id = callback.from_user.id
        lang_id = await category_service.get_user_language(user_id)

        categories = await category_service.get_root_battles()
        keyboard = await keyboard_service.create_keyboard(categories, lang_id, "category")
        await callback.message.edit_text(TEXT_QUIZ[lang_id], reply_markup=keyboard)
        await RoomQuizStates.selecting_category.set()
    except Exception as e:
        logger.error(f"Error starting quiz: {e}")
        await callback.message.answer("Xatolik yuz berdi")


@dp.message_handler(state=QuizStates.QUIZ_START)
async def handle_quiz_start(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        quiz_id = data['quiz_id']
        quiz_number = data['quiz_number']

        questions = await quiz_service.get_quiz_questions(quiz_id, quiz_number)
        await state.update_data(questions=questions, current_index=0)

        await send_question(message, state)
    except Exception as e:
        logger.error(f"Error in quiz start: {e}")
        await message.answer("Xatolik yuz berdi")