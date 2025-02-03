from aiogram import types

from handlers.users.texts import BTN_BOOK, BTN_BATTLE, BTN_INFO, BTN_SETTINGS, BTN_ABOUT_US


class MenuService:
   def __init__(self, db):
       self.db = db

   async def get_main_menu(self, user_id: int):
       lang_id = self.db.get_user_language_id(user_id)
       keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
       keyboard.add(BTN_BOOK[lang_id])
       buttons_menu_row1 = [BTN_BATTLE[lang_id], BTN_ABOUT_US[lang_id]]
       buttons_menu_row2 = [BTN_INFO[lang_id], BTN_SETTINGS[lang_id]]
       keyboard.add(*buttons_menu_row1)
       keyboard.add(*buttons_menu_row2)
       if await self._is_admin(user_id):
           keyboard.add(*['All users', 'Broadcast'])

       return keyboard

   async def _is_admin(self, user_id: int) -> bool:
       user_ids = self.db.get_all_setadmin_user_ids()
       admin_ids = []
       for id in user_ids:
           admin_id = self.db.get_chat_id_by_user_id(id)
           admin_ids.append(admin_id)
       return user_id in admin_ids