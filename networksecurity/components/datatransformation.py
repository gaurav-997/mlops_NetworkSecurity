import os 
import sys
from sklearn.impute import KNNImputer
from sklearn.pipeline import Pipeline
import pandas as pd
import numpy as np


from networksecurity.entity.config_entity import DataTransformationConfig
from networksecurity.entity.artifact_entity import DataValidationAritfact ,ModelTrainerArtifact
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException

from networksecurity.constant import training_pipeline
from networksecurity.utils.main_utils.utils import save_numpy_array_data,save_object

class DataTransformation:
    def __init__(self , data_validation_artifact:DataValidationAritfact , data_transformation_config:DataTransformationConfig):
        try:
            self.data_validation_artifact = data_validation_artifact
            self.data_validation_artifact = data_validation_artifact
        except Exception as e:
            raise CustomException(e,sys)
        
    def read_validated_data(self,filepath:pd.DataFrame):
        try:
            data = pd.read_csv(filepath)
            df = pd.DataFrame(data)
            return df
        
        except Exception as e:
            raise CustomException(e,sys)
    
    # implementing KNN imputer 
    def get_data_transformer_object(cls)->Pipeline:
        try:
            imputer = KNNImputer(**training_pipeline.DATA_TRANSFORMATION_IMPUTER_PARAMS)
            processor = Pipeline(imputer)
            return processor
        
        except Exception as e:
            raise CustomException(e,sys)
        
    def initiate_data_transformation(self):
        try:
            logging.info("Data transformation started")
            train_df = self.read_validated_data(filepath=self.data_validation_artifact.valid_train_file_path)
            test_df = self.read_validated_data(filepath=self.data_validation_artifact.valid_train_file_path)
            
            
        except Exception as e:
            raise CustomException(e,sys)
