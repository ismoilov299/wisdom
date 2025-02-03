from aiogram.dispatcher.filters.state import State, StatesGroup

class QuizStates(StatesGroup):
   SELECTING_CATEGORY = State()
   SELECTING_BATTLE = State()
   ENTERING_NUMBER = State()
   ENTERING_TIME = State()
   IN_PROGRESS = State()
   WAITING_ANSWER = State()
   FINISHED = State()

class RoomStates(StatesGroup):
   CREATING = State()
   WAITING_PLAYERS = State()
   IN_PROGRESS = State()
   FINISHED = State()