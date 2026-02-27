import os
import sys 
import pandas as pd
from scipy.stats import ks_2samp

from networksecurity.constant import training_pipeline
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact,DataValidationAritfact
from networksecurity.constant import training_pipeline
from networksecurity.utils.main_utils.utils import read_yaml,write_data

class DataValidation:
    def __init__(self,data_ingestion_artifact:DataIngestionArtifact , data_validation_config:DataValidationConfig):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
        except Exception as e:
            raise CustomException(e,sys)
     
    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        """
        Validates that the number of columns in the dataframe matches the number of columns defined in the schema.yaml file.
        """
        try:
            schema = read_yaml(training_pipeline.SCHEMA_FILE_PATH)
            schema_columns = schema.get('columns', [])
            number_of_columns = len(schema_columns)
            if len(dataframe.columns) == number_of_columns:
                return True
            else:
                return False
        except Exception as e:
            raise CustomException(e, sys)
        
    
    def numerical_columns_exists(self, dataframe: pd.DataFrame) -> bool:
        """
        Checks if all numerical columns defined in the schema numerical exist in the dataframe.
        """
        try:
            schema = read_yaml(training_pipeline.SCHEMA_FILE_PATH)
            schema_numerical_columns = schema.get('numerical_columns', [])
            dataframe_columns = set(dataframe.columns)
            missing_columns = [col for col in schema_numerical_columns if col not in dataframe_columns]
            if not missing_columns:
                return True
            else:
                return False
        except Exception as e:
            raise CustomException(e, sys)
        
    def detect_dataset_drift(self, base_df, current_df, threshold=0.05) -> bool:
        """
        Detects data drift between base_df and current_df using the Kolmogorov-Smirnov test for each numerical column.
        Returns True if no drift is detected, False otherwise. Saves a detailed drift report.
        Only compare columns present in both DataFrames.
        Focus on numerical columns.
        Handle missing columns and insufficient data.
        Return True if no drift is detected, False otherwise.
        Save a detailed drift report including missing columns.

        """
        try:
            status = True
            report = {}
            # Only check columns present in both DataFrames
            common_columns = [col for col in base_df.columns if col in current_df.columns]
            # Optionally, filter to numerical columns only (float, int)
            numerical_columns = [col for col in common_columns if pd.api.types.is_numeric_dtype(base_df[col]) and pd.api.types.is_numeric_dtype(current_df[col])]
            for column in numerical_columns:
                d1 = base_df[column].dropna()
                d2 = current_df[column].dropna()
                if len(d1) == 0 or len(d2) == 0:
                    # Not enough data to compare
                    report[column] = {"p_value": None, "drift_status": "insufficient_data"}
                    continue
                is_same_dist = ks_2samp(d1, d2)
                if is_same_dist.pvalue >= threshold:
                    drift_found = False
                else:
                    drift_found = True
                    status = False
                report[column] = {
                    "p_value": float(is_same_dist.pvalue),
                    "drift_status": drift_found
                }
            # Optionally, note columns missing in either DataFrame
            missing_in_current = [col for col in base_df.columns if col not in current_df.columns]
            missing_in_base = [col for col in current_df.columns if col not in base_df.columns]
            if missing_in_current:
                report["missing_in_current_df"] = missing_in_current
            if missing_in_base:
                report["missing_in_base_df"] = missing_in_base

            drift_report_file_path = self.data_validation_config.drift_report_file_path
            dir_path = os.path.dirname(drift_report_file_path)
            os.makedirs(dir_path, exist_ok=True)
            write_data(file_path=drift_report_file_path, content=report)
            return status
        except Exception as e:
            raise CustomException(e, sys)
        
          
          
    def initiate_data_validation(self):
        try:
            pass
        except Exception as e:
            raise CustomException(e,sys)

