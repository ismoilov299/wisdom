# handlers/users/quiz_handlers.py faylining to'liq versiyasi
import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from constants.error_messages import ERRORS
from handlers.users.texts import TEXT_ALL, TEXT_QUIZ
from loader import dp, bot
from utils.logging_utils import logger

from states.room_states import RoomQuizStates, GroupQuizStates, QuizStates
from services.quiz_service import QuizService
from services.keyboard_service import KeyboardService
from services.category_service import CategoryService

quiz_service = QuizService()
keyboard_service = KeyboardService()
category_service = CategoryService()

PRODUCT_PREFIX = 'product_'
TEST_PREFIX = 'test_'

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


@dp.callback_query_handler(lambda c: c.data.startswith('category_'), state=RoomQuizStates.selecting_category)
async def handle_quiz_category(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split('_')
        category_id = int(parts[1])
        user_id = callback.from_user.id
        lang_id = await category_service.get_user_language(user_id)

        # Kategoriya uchun sub-kategoriya va testlarni tekshirish
        subcategories = await quiz_service.get_subcategories(category_id)

        if subcategories:
            # Agar subkategoriyalar bo'lsa ularni ko'rsatish
            keyboard = await keyboard_service.create_keyboard(subcategories, lang_id, "subcategory")
            await callback.message.edit_text(TEXT_QUIZ[lang_id], reply_markup=keyboard)
        else:
            # Subkategoriyalar bo'lmasa, testlarni tekshirish
            questions = await quiz_service.get_questions_by_battle_id(category_id)
            if questions:
                # Testlar topilsa savollar sonini so'rash
                await state.update_data(category_id=category_id)
                await callback.message.answer("Savollar sonini kiriting (masalan: 30):")
                await RoomQuizStates.quiz_number.set()
            else:
                await callback.message.answer("Bu bo'limda testlar mavjud emas")

    except Exception as e:
        logger.error(f"Error in quiz category selection: {e}")
        await callback.message.answer("Xatolik yuz berdi")

# handlers/users/quiz_handlers.py davomi

@dp.callback_query_handler(lambda c: c.data.startswith(TEST_PREFIX))
async def handle_test(callback: CallbackQuery, state: FSMContext):
   try:
       parts = callback.data.split('_')
       logger.info(f"Callback data parts: {parts}")
       parent_id = int(parts[1])
       user_id = callback.from_user.id
       lang_id = await category_service.get_user_language(user_id)
       is_admin = await category_service.is_admin(user_id)

       result = await quiz_service.handle_test_selection(parent_id)

       if result['type'] == 'categories':
           keyboard = await keyboard_service.create_keyboard(
               result['data'],
               lang_id,
               "subcategory",
               is_admin=is_admin
           )
           await callback.message.edit_text(TEXT_ALL[lang_id], reply_markup=keyboard)
       elif result['type'] == 'questions':
           await quiz_service.start_quiz_battle(callback.message, state, result['data'])
       else:
           await callback.message.answer("Bu bo'limda testlar mavjud emas")

   except Exception as e:
       logger.error(f"Test handler error: {e}", exc_info=True)
       await callback.message.answer("Xatolik yuz berdi")


# quiz_handlers.py
@dp.message_handler(state=QuizStates.ENTERING_NAME)
async def process_quiz_name(message: types.Message, state: FSMContext):
    try:
        user_name = message.text
        data = await state.get_data()

        # State ga ismni saqlash
        await state.update_data(name=user_name)

        # Adminga xabar yuborish va test boshlash tugmasi
        battle = await quiz_service.get_battle_name(data['quiz_id'])
        admin_keyboard = InlineKeyboardMarkup()
        admin_keyboard.add(InlineKeyboardButton(
            text="Testni boshlash",
            callback_data=f"start_quiz_for_all_{data['unique_id']}"
        ))

        owner_message = (
            f"🎯 {battle} ({data['quiz_name']}) testiga\n"
            f"👤 {user_name} qo'shildi!\n\n"
            "Testni boshlash uchun tugmani bosing:"
        )
        await bot.send_message(
            data['owner_id'],
            owner_message,
            reply_markup=admin_keyboard
        )

        # Foydalanuvchiga kutish xabari
        await message.answer(
            f"Test nomi: {data['quiz_name']}\n"
            f"Test vaqti: {data['quiz_time']} soniya\n"
            f"Savollar soni: {data['quiz_number']}\n"
            "Admin testni boshlaguncha kuting..."
        )

        # Foydalanuvchini bazaga qo'shish
        await quiz_service.add_quiz_participant(
            unique_id=data['unique_id'],
            user_id=message.from_user.id,
            user_name=user_name
        )

        await QuizStates.WAITING_START.set()

    except Exception as e:
        logger.error(f"Error processing name: {e}")
        await message.answer("Xatolik yuz berdi")



# quiz_handlers.py
@dp.callback_query_handler(lambda c: c.data.startswith('start_quiz_for_all_'))
async def start_quiz_for_all(callback: CallbackQuery, state: FSMContext):
    try:
        unique_id = callback.data.split('_')[-1]
        logger.info(f"Starting quiz for unique_id: {unique_id}")

        # Active quizzes ni quiz_service orqali tekshiramiz
        active_quiz = await quiz_service.get_active_quiz(unique_id)
        if active_quiz and active_quiz.get('started', False):
            await callback.message.answer("Test allaqachon boshlangan!")
            return

        participants = await quiz_service.get_quiz_participants(unique_id)
        quiz_data = await quiz_service.get_quiz_questions(unique_id)

        if not participants:
            await callback.message.answer("Hozircha qatnashchilar yo'q")
            return

        # Quiz ni active qilish
        await quiz_service.set_quiz_started(unique_id)

        await callback.message.edit_text("Test boshlandi! ✅")

        # Har bir qatnashchiga test yuborish
        send_tasks = []
        for participant in participants:
            user_id = participant[2]  # chat_id
            send_tasks.append(
                bot.send_message(user_id, "Test boshlandi! Omad! 🎯")
            )
            send_tasks.append(
                quiz_service.start_quiz_for_user(user_id, quiz_data)
            )

        await asyncio.gather(*send_tasks)

    except Exception as e:
        logger.error(f"Error starting quiz for all: {e}", exc_info=True)
        await callback.message.answer("Xatolik yuz berdi")


@dp.message_handler(state=QuizStates.WAITING_ANSWER)
async def process_answer(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        if not data.get('test_started', False):
            return

        is_correct = await quiz_service.process_answer(
            message.text,
            data['correct_answer']
        )
        await quiz_service.save_answer(state, is_correct)
        await quiz_service.send_next_question(message, state)
    except Exception as e:
        logger.error(f"Answer processing error: {e}")

@dp.message_handler(state=QuizStates.QUIZ_START)
async def handle_quiz_start(message: types.Message, state: FSMContext):
   try:
       data = await state.get_data()
       quiz_id = data['quiz_id']
       quiz_number = data['quiz_number']

       questions = await quiz_service.get_quiz_questions(quiz_id, quiz_number)
       await state.update_data(questions=questions, current_index=0)
       await quiz_service.send_next_question(message, state)
   except Exception as e:
       logger.error(f"Error in quiz start: {e}")
       await message.answer("Xatolik yuz berdi")


# handlers/users/quiz_handlers.py davomi

@dp.callback_query_handler(state=RoomQuizStates.selecting_category)
async def select_category(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info("Selecting quiz category")
        parts = callback.data.split('_')
        category_id = int(parts[1])

        await state.update_data(category_id=category_id)
        await callback.message.answer("Savollar sonini kiriting (masalan: 30):")
        await RoomQuizStates.quiz_number.set()

    except Exception as e:
        logger.error(f"Error in category selection: {e}")
        await callback.message.answer("Xatolik yuz berdi")


@dp.message_handler(state=RoomQuizStates.quiz_number)
async def process_quiz_number(message: types.Message, state: FSMContext):
    try:
        if not message.text.isdigit():
            return await message.answer("Iltimos, raqam kiriting")

        quiz_number = int(message.text)
        await state.update_data(quiz_number=quiz_number)
        await message.answer("Test vaqtini kiriting (sekundda, masalan: 30):")
        await RoomQuizStates.quiz_time.set()

    except Exception as e:
        logger.error(f"Error processing quiz number: {e}")
        await message.answer("Xatolik yuz berdi")


@dp.message_handler(state=RoomQuizStates.quiz_time)
async def process_quiz_time(message: types.Message, state: FSMContext):
    try:
        if not message.text.isdigit():
            return await message.answer("Iltimos, raqam kiriting")

        data = await state.get_data()
        quiz_time = int(message.text)

        unique_id, quiz_name = await quiz_service.create_quiz(
            quiz_id=data['category_id'],
            quiz_number=data['quiz_number'],
            quiz_time=quiz_time,
            user_id=message.from_user.id
        )

        await message.answer(
            f"🎯 Test yaratildi!\n\n"
            f"📝 Test nomi: {quiz_name}\n"
            f"📊 Savollar soni: {data['quiz_number']}\n"
            f"⏱ Vaqt: {quiz_time} soniya"
        )


        invite_link = await quiz_service.generate_invite_link(
            user_id=message.from_user.id,
            quiz_id=data['category_id'],
            unique_id=unique_id,
            quiz_number=data['quiz_number'],
            quiz_time=quiz_time,
            quiz_name=quiz_name
        )

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            text="Testga havola",
            url=invite_link
        ))

        await message.answer("🔗 Havolani ulashing:", reply_markup=keyboard)
        await state.finish()

    except Exception as e:
        logger.error(f"Error processing quiz time: {e}")
        await message.answer("Xatolik yuz berdi")


@dp.callback_query_handler(lambda c: c.data.startswith('personal_result_'))
async def show_personal_results(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_name = callback.data.split('_')[2]
        data = await state.get_data()

        detailed_results = await quiz_service.get_detailed_results(
            user_name,
            data.get('answers', []),
            data.get('questions', [])
        )

        await callback.message.edit_text(detailed_results)

    except Exception as e:
        logger.error(f"Error showing personal results: {e}")


@dp.callback_query_handler(lambda c: c.data == "group_results")
async def show_group_results(callback: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        unique_id = data.get('unique_id')

        group_results = await quiz_service.get_group_results(unique_id)
        await callback.message.edit_text(group_results)

    except Exception as e:
        logger.error(f"Error showing group results: {e}")