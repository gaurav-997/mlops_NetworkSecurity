import os
import sys
import yaml
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException

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