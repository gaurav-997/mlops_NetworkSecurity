import os 
import pandas as pd
import sys
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException

from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact

from networksecurity.constant import training_pipeline

from sklearn.model_selection import train_test_split

class DataIngestion:
    def __init__(self,data_ingestion_config:DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise CustomException(e,sys)
        
    def read_data(self,filepath:str):
        try:
            data = pd.read_csv(filepath)
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            raise CustomException(e,sys)
        
    def export_raw_data_to_feature_store(self,dataframe:pd.DataFrame):
        try:
            feature_store_file_path= self.data_ingestion_config.feature_store_dir
            os.makedirs(feature_store_file_path,exist_ok=True)
            dataframe.to_csv(feature_store_file_path,index=False,header=True)
            return dataframe
            
        except Exception as e:
            raise CustomException(e,sys)
        
    def split_data_as_train_test(self,dataframe:pd.DataFrame):
        try:
            train_df,test_df = train_test_split(dataframe,test_size=self.data_ingestion_config.train_test_split_ratio,random_state=42)
            
            dir_path = self.data_ingestion_config.data_ingested_dir
            os.makedirs(dir_path,exist_ok=True)
            
            train_df.to_csv(self.data_ingestion_config.train_file_path,index=False,header=True)
            test_df.to_csv(self.data_ingestion_config.test_file_path,index=False,header=True)
                        
        except Exception as e:
            raise CustomException(e,sys)
        
    
    
    def initiate_data_ingestion(self):
        try:
            raw_data = self.read_data(filepath="Network_data\phisingData.csv")
            self.export_raw_data_to_feature_store(dataframe=raw_data)
            self.split_data_as_train_test(dataframe=raw_data)
            dataingestion_artifact = DataIngestionArtifact(train_file_path=self.data_ingestion_config.train_file_path,test_file_path=self.data_ingestion_config.test_file_path)
            return dataingestion_artifact
        except Exception as e:
            raise CustomException(e,sys)