"""
Network Model Estimator
Wraps preprocessor and model for prediction pipeline.
"""
import sys
import numpy as np
import pandas as pd
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException


class NetworkModel:
    """
    Network Security Model class that wraps preprocessing and prediction.
    """
    
    def __init__(self, preprocessor, model):
        """
        Initialize NetworkModel with preprocessor and model.
        
        Args:
            preprocessor: Preprocessing pipeline object
            model: Trained ML model
        """
        try:
            self.preprocessor = preprocessor
            self.model = model
            logging.info("NetworkModel initialized successfully")
        except Exception as e:
            raise CustomException(e, sys)
    
    def predict(self, dataframe: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on input dataframe.
        
        Args:
            dataframe: Input pandas DataFrame
            
        Returns:
            np.ndarray: Predictions
        """
        try:
            logging.info("Starting prediction in NetworkModel")
            
            # Apply preprocessing
            transformed_data = self.preprocessor.transform(dataframe)
            logging.info(f"Data transformed. Shape: {transformed_data.shape}")
            
            # Make predictions
            predictions = self.model.predict(transformed_data)
            logging.info(f"Predictions completed. Total samples: {len(predictions)}")
            
            return predictions
            
        except Exception as e:
            raise CustomException(e, sys)
