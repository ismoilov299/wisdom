from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from constants.error_messages import ERRORS
from handlers.users import texts
from handlers.users.texts import BTN_LANG_UZ, BTN_LANG_RU
from loader import bot
from services.quiz_service import QuizService
from states.room_states import QuizStates
from states.userStates import UserStates
from utils.logging_utils import logger
quiz_service = QuizService()

class AuthService:
    def __init__(self, db):
        self.db = db

    async def _get_start_quiz_keyboard(self):

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Boshlash", callback_data="start_quiz")
        )
        return keyboard

    # auth_service.py
    async def _handle_quiz_link(self, message, state, args):
        try:
            user_id = int(args[0])  # admin id
            quiz_id = int(args[2])
            unique_id = args[3]  # test unique id
            quiz_number = int(args[5])
            quiz_time = int(args[7])
            quiz_name = args[9]

            await state.update_data({
                'owner_id': user_id,
                'quiz_id': quiz_id,
                'unique_id': unique_id,  # unique id saqlaymiz
                'quiz_number': quiz_number,
                'quiz_time': quiz_time,
                'quiz_name': quiz_name
            })

            await message.answer("Ismingizni kiriting:")
            await QuizStates.ENTERING_NAME.set()

        except Exception as e:
            logger.error(f"Error handling quiz link: {e}")
            await message.answer(ERRORS['general'])

    async def _validate_args(self, args: list) -> bool:
        try:
            if len(args) < 10:
                return False

            user_id = args[0]
            quiz_command = args[1]
            quiz_id = args[2]
            unique_id = args[3]
            number_command = args[4]
            quiz_number = args[5]
            time_command = args[6]
            quiz_time = args[7]
            name_command = args[8]
            quiz_name = args[9]

            return (quiz_command == 'quiz' and
                    number_command == 'number' and
                    time_command == 'time' and
                    name_command == 'name' and
                    user_id.isdigit() and
                    quiz_id.isdigit() and
                    quiz_number.isdigit() and
                    quiz_time.isdigit())

        except Exception as e:
            logger.error(f"Args validation error: {e}")
            return False

    async def process_deep_link(self, message, state, args):
        try:
            args = args.split('_')
            if await self._validate_args(args):  # await qo'shamiz
                await self._handle_quiz_link(message, state, args)
            else:
                await message.answer("Noto'g'ri havola")
        except Exception as e:
            logger.error(f"Deep link error: {e}")



    async def _get_language_keyboard(self):

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(
            KeyboardButton(BTN_LANG_UZ),
            KeyboardButton(BTN_LANG_RU),
        )
        return keyboard

    async def start_registration(self, message, state):
        await UserStates.IN_LANG.set()
        keyboard = await self._get_language_keyboard()
        await message.answer(texts.WELCOME_TEXT)
        await message.answer(texts.CHOOSE_LANG, reply_markup=keyboard)