# utils/logging_utils.py
import logging
import os
from datetime import datetime

def setup_logger():
   logger = logging.getLogger('bot_logger')
   logger.setLevel(logging.INFO)

   logs_dir = 'logs'
   if not os.path.exists(logs_dir):
       os.makedirs(logs_dir)

   log_file = os.path.join(logs_dir, f'bot_{datetime.now().strftime("%Y%m%d")}.log')
   file_handler = logging.FileHandler(log_file)
   file_handler.setLevel(logging.INFO)

   # Format
   formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
   file_handler.setFormatter(formatter)

   logger.addHandler(file_handler)
   return logger

logger = setup_logger()