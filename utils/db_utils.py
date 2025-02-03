import logging
from functools import wraps
from typing import Callable, Any
from sqlite3 import Error

logger = logging.getLogger(__name__)

def safe_db_query(func: Callable) -> Callable:
   @wraps(func)
   async def wrapper(*args, **kwargs) -> Any:
       try:
           return await func(*args, **kwargs)
       except Error as e:
           logger.error(f"Database error in {func.__name__}: {str(e)}")
           raise
       except Exception as e:
           logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
           raise
   return wrapper