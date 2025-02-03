# states/room_states.py
from aiogram.dispatcher.filters.state import State, StatesGroup

class RoomQuizStates(StatesGroup):
   selecting_category = State()
   selecting_battle = State() 
   quiz_number = State()
   quiz_time = State()
   waiting_players = State()

class GroupQuizStates(StatesGroup):
   waiting_answer = State()
   next_question = State() 
   finished = State()



class QuizStates(StatesGroup):
   WAITING_START = State()
   ENTERING_NAME = State()
   QUIZ_START = State()
   WAITING_ANSWER = State()
   FINISHED = State()