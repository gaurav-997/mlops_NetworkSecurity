import os
import sys
import yaml
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
import pickle

import numpy as np

def read_yaml(filepath:str):
    try:
        with open(filepath, "rb") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise CustomException(e,sys)
    

def write_data(filepath:str, content:object):
    try:
        os.makedirs(filepath , exist_ok= True)
        with open(filepath,"w") as f:
            yaml.dump(content,f)
    except Exception as e:
        raise CustomException(e,sys)
    
def save_numpy_array_data(filepath,array:np.array):
    try:
        os.makedirs(filepath,exist_ok=True)
        with open(filepath,'wb') as f:
            return np.save(f,array)
    except Exception as e:
        raise CustomException(e,sys)
    
def save_object(file_path: str, obj: object) -> None:
    try:
        logging.info("Entered the save_object method of MainUtils class")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file_obj:
            pickle.dump(obj, file_obj)
        logging.info("Exited the save_object method of MainUtils class")
    except Exception as e:
        raise CustomException(e, sys) from e
    
def load_object(file_path: str, ) -> object:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} is not exists")
        with open(file_path, "rb") as file_obj:
            print(file_obj)
            return pickle.load(file_obj)
    except Exception as e:
        raise CustomException(e, sys) from e
    
def load_numpy_array_data(file_path: str) -> np.array:
    """
    load numpy array data from file
    file_path: str location of file to load
    return: np.array data loaded
    """
    try:
        with open(file_path, "rb") as file_obj:
            return np.load(file_obj)
    except Exception as e:
        raise CustomException(e, sys) from e