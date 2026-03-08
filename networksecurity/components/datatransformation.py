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
            
            # spliting train and test data into input feature and traget feature , replacing -1 with 0 in target feature
            input_train_df_features = train_df.drop(columns=[training_pipeline.TARGET_COLUMN],axis=1)
            target_train_df_features = train_df[training_pipeline.TARGET_COLUMN]
            target_train_df_features = target_train_df_features.replace(-1 ,0)
            
            input_feature_test_df = test_df.drop(columns=[training_pipeline.TARGET_COLUMN], axis=1)
            target_feature_test_df = test_df[training_pipeline.TARGET_COLUMN]
            target_feature_test_df = target_feature_test_df.replace(-1, 0)
            
            # applying KNN imputer to impute missing values in input features
            imputer_object = self.get_data_transformer_object()
            imputer_object.fit(input_train_df_features)
            transformed_input_train_df_features = imputer_object.transform(input_train_df_features)
            transformed_input_feature_test_df = imputer_object.transform(input_feature_test_df)
            
            # saving the imputer object and transformed data
            save_object(file_path=self.data_transformation_config.transformed_object_file_path, obj=imputer_object)
            save_numpy_array_data(file_path=self.data_transformation_config.transformed_train_file_path, array=transformed_input_train_df_features)
            save_numpy_array_data(file_path=self.data_transformation_config.transformed_test_file_path, array=transformed_input_feature_test_df)

            # preparing artifact
            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path
            )
            return data_transformation_artifact

        except Exception as e:
            raise CustomException(e,sys)
