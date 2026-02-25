from datetime import datetime
import os
import sys
from networksecurity.constant import training_pipeline
from networksecurity.logging import logger
from networksecurity.exception import CustomException

class TrainingPipelineConfig:
    def __init__(self,):
        try:
            pass
        except Exception as e:
            raise CustomException(e,sys)