# utils/quiz_helpers.py
from aiogram import types
from aiogram.dispatcher import FSMContext



class QuizHelper:
   @staticmethod
   async def save_answer(state: FSMContext, is_correct: bool):
       data = await state.get_data()
       answers = data.get('answers', [])
       answers.append(is_correct)
       await state.update_data(
           answers=answers,
           answered=True
       )

   @staticmethod
   async def send_next_question(message: types.Message, state: FSMContext):
       data = await state.get_data()
       questions = data['questions']
       current_index = data.get('current_index', 0)

       if current_index < len(questions):
           question = questions[current_index]
           await state.update_data(
               current_index=current_index + 1,
               correct_answer=question['question'],
               answered=False
           )
           await QuizState.waiting_for_answer.set()
           await message.answer(f"{current_index + 1}/{len(questions)}\n{question['answer_a']}")
       else:
           await end_quiz(message, state)