# services/category_service.py
from typing import List, Tuple
from loader import db
from utils.db_utils import safe_db_query
from utils.logging_utils import logger


class CategoryService:
   def __init__(self):
       self.db = db

   @safe_db_query
   async def get_user_language(self, user_id: int) -> int:
       return self.db.get_user_language_id(user_id)

   @safe_db_query
   async def get_root_categories(self) -> List[Tuple]:
       return self.db.get_root_categories()

   @safe_db_query
   async def get_root_battles(self) -> List[Tuple]:
       return self.db.get_root_battle()

   @safe_db_query
   async def is_admin(self, user_id: int) -> bool:
       try:
           # To'g'ridan to'g'ri chat_id orqali tekshirish
           return self.db.check_is_admin(user_id)
       except Exception as e:
           logger.error(f"Error checking admin status: {e}")
           return False

   @safe_db_query
   async def get_subcategories(self, parent_id: int) -> List[Tuple]:
       return self.db.get_categories_by_parent_id(parent_id)

   @safe_db_query
   async def get_battles(self, parent_id: int) -> List[Tuple]:
       return self.db.get_battle_by_parent_id(parent_id)