import os, sys 
import numpy as np
import pandas as pd
import shutil
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
from networksecurity.entity.config_entity import ModelPusherConfig
from networksecurity.entity.artifact_entity import ModelPusherArtifact , ModelEvaluationArtifact
from networksecurity.utils.main_utils.utils import save_object, load_object

class ModelPusher:
    def __init__(self,model_pusher_config:ModelPusherConfig,model_evaluation_artifact:ModelEvaluationArtifact):
        try:
            self.model_pusher_config = model_pusher_config
            self.model_evaluation_artifact = model_evaluation_artifact
        except Exception as e:
            raise CustomException(e,sys)

    # copy best model file to model_pusher_dir from model_evaluation_artifact
    def copy_best_model(self):
        try:
            os.makedirs(self.model_pusher_config.model_pusher_dir, exist_ok=True)
            shutil.copy(self.model_evaluation_artifact.best_model_path, self.model_pusher_config.model_file_path)
        except Exception as e:
            raise CustomException(e,sys)

    # copy preprocessing.pkl file to model_pusher_dir from data_transformation_artifact
    def copy_preprocessing_object(self):
        try:
            shutil.copy(self.data_transformation_artifact.preprocessing_object_file_path, self.model_pusher_config.model_pusher_dir)
        except Exception as e:
            raise CustomException(e,sys)

    # def push_model(self):
    #     try:
    #         shutil.copy(self.model_pusher_config.model_file_path, self.model_pusher_config.training_bucket_name)
    #     except Exception as e:
    #         raise CustomException(e,sys)

        
    def initiate_model_pusher(self)->ModelPusherArtifact:
        try:
            self.copy_best_model()
            self.copy_preprocessing_object()
            model_pusher_artifact = ModelPusherArtifact(
                is_pushed=True,
                model_dir=self.model_pusher_config.model_pusher_dir,
                saved_model_path=self.model_pusher_config.model_file_path
            )
            return model_pusher_artifact
        except Exception as e:
            raise CustomException(e,sys)