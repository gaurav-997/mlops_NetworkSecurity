import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

log_dir = os.path.join(os.getcwd(),"Logs")
os.makedirs(log_dir,exist_ok=True)
log_file = os.path.join(log_dir,f"{datetime.now().strftime('%m_%d_%Y_%H')}.log")

logger = logging.getLogger("mlops_networksecurity")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] %(lineno)d %(name)s - %(levelname)s - %(message)s")

file_handler = RotatingFileHandler(filename=log_file)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)