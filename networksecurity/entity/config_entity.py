from datetime import datetime
import os
import sys
from networksecurity.constant import training_pipeline
from networksecurity.logging import logger
from networksecurity.exception import CustomException

class TrainingPipelineConfig:
    def __init__(self,timestamp= datetime.now()):
        try:
            timestamp = timestamp.strftime(format='%m_%d_%Y_%H_%M_%S')
            self.artifact_name = training_pipeline.ARTIFACT_DIR_NAME
            self.artifact_dir = os.path.join(self.artifact_name,timestamp)
            self.pipeline_name = training_pipeline.PIPELINE_NAME
        except Exception as e:
            raise CustomException(e,sys)
        
class DataIngestionConfig:
    def __init__(self,trainingpipelineconfig:TrainingPipelineConfig):
        try:
            self.data_ingestion_dir = os.path.join(trainingpipelineconfig.artifact_dir,training_pipeline.DATA_INGESTION_DIR_NAME)
            self.feature_store_dir = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_INGESTED_DIR)
            self.data_ingested_dir = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_DIR_NAME)
            self.train_file_path = os.path.join(self.data_ingested_dir,training_pipeline.TRAIN_FILE_NAME)
            self.test_file_path = os.path.join(self.data_ingested_dir,training_pipeline.TEST_FILE_NAME)
            self.train_test_split_ratio = training_pipeline.DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO
            
            
        except Exception as e:
            raise CustomException(e,sys)