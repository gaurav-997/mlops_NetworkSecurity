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
            self.feature_store_dir = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_FEATURE_STORE)
            self.data_ingested_dir = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_DIR_NAME)
            self.train_file_path = os.path.join(self.data_ingested_dir,training_pipeline.TRAIN_FILE_NAME)
            self.test_file_path = os.path.join(self.data_ingested_dir,training_pipeline.TEST_FILE_NAME)
            self.train_test_split_ratio = training_pipeline.DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO
            
        except Exception as e:
            raise CustomException(e,sys)
        
class DataValidationConfig:
    def __init__(self,trainingpipelineconfig:TrainingPipelineConfig):
        try:
            self.data_validation_dir = os.path.join(trainingpipelineconfig.artifact_dir,training_pipeline.DATA_VALIDATION_DIR_NAME)
            self.valid_data_dir = os.path.join(self.data_validation_dir,training_pipeline.DATA_VALIDATION_VALID_DIR)
            self.invalid_data_dir = os.path.join(self.data_validation_dir,training_pipeline.DATA_VALIDATION_INVALID_DIR)
            self.data_drift_dir = os.path.join(self.data_validation_dir,training_pipeline.DATA_VALIDATION_DRIFT_REPORT_DIR)
            self.data_drift_file_name = training_pipeline.DATA_VALIDATION_DRIFT_REPORT_FILE_NAME
            self.valid_train_file_path = os.path.join(self.valid_data_dir,training_pipeline.TRAIN_FILE_NAME)
            self.valid_test_file_path = os.path.join(self.valid_data_dir,training_pipeline.TEST_FILE_NAME)
            self.invalid_train_file_path = os.path.join(self.invalid_data_dir,training_pipeline.TRAIN_FILE_NAME)
            self.invalid_test_file_path = os.path.join(self.invalid_data_dir,training_pipeline.TEST_FILE_NAME)
        except Exception as e:
            raise CustomException(e,sys)
        
class DataTransformationConfig:
    def __init__(self,trainingpipelineconfig:TrainingPipelineConfig):
        try:
            self.data_transformation_dir: str = os.path.join( trainingpipelineconfig.artifact_dir,training_pipeline.DATA_TRANSFORMATION_DIR_NAME )
            self.transformed_train_file_path: str = os.path.join( self.data_transformation_dir,training_pipeline.DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR,
            training_pipeline.TRAIN_FILE_NAME.replace("csv", "npy"),)
            self.transformed_test_file_path: str = os.path.join(self.data_transformation_dir,  training_pipeline.DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR,
            training_pipeline.TEST_FILE_NAME.replace("csv", "npy"), )
            self.transformed_object_file_path: str = os.path.join( self.data_transformation_dir, training_pipeline.DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR,
            training_pipeline.PREPROCESSING_OBJECT_FILE_NAME,)
        except Exception as e:
            raise CustomException(e,sys)
    
class ModelTrainerConfig:
    def __init__(self,trainingpipelineconfig:TrainingPipelineConfig):
        try:
            self.model_trainer_dir: str = os.path.join(trainingpipelineconfig.artifact_dir, training_pipeline.MODEL_TRAINER_DIR_NAME)
            self.trained_model_file_path: str = os.path.join(self.model_trainer_dir, training_pipeline.MODEL_TRAINER_TRAINED_MODEL_DIR,training_pipeline.MODEL_TRAINER_TRAINED_MODEL_NAME)
            self.expected_accuracy: float = training_pipeline.MODEL_TRAINER_EXPECTED_SCORE
            self.overfitting_underfitting_threshold = training_pipeline.MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD
        except Exception as e:
            raise CustomException(e,sys)

class ModelEvaluationConfig:
    def __init__(self, trainingpipelineconfig: TrainingPipelineConfig):
        try:
            self.model_evaluation_dir: str = os.path.join(
                trainingpipelineconfig.artifact_dir, training_pipeline.MODEL_EVALUATION_DIR_NAME
            )
            self.report_file_path: str = os.path.join(
                self.model_evaluation_dir, training_pipeline.MODEL_EVALUATION_REPORT_NAME
            )
            self.change_threshold: float = training_pipeline.MODEL_EVALUATION_CHANGED_THRESHOLD_SCORE
            self.best_model_dir: str = training_pipeline.BEST_MODEL_DIR
            self.best_model_file_path: str = os.path.join(
                training_pipeline.BEST_MODEL_DIR, training_pipeline.BEST_MODEL_FILE_NAME
            )
        except Exception as e:
            raise CustomException(e, sys)