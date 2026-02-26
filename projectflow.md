# prepare setup.py + logger + exception handling

# Common constants
path -  networksecurity/constant/training_pipeline/__init__.py
a. Define common constants to be used in project
 like TARGET_COLUMN , ARTIFACT_DIR_NAME , DATA_FILE_NAME , PIPELINE_NAME 

# DataIngestion Constants decleration 
path - networksecurity/constant/training_pipeline/__init__.py 
a. Define the constants with their values used in Data ingestion
   e.g data_collection_name , data_ingestion_dir , feature store file path , train-test file path and ratio 

que- if I am not using mongoDB , I am using my local system for initial raw data , So I dont need collection name

# DataIngestion config entity 
path - networksecurity/entity/config_entity.py
a. Define Data ingestion config class and TraningPipelineConfig class 
b. refer the data defined in constants 
e.g self.pipeline_name = training_pipeline.PIPELINE_NAME 
    self.target_column = training_pipeline.TARGET_COLUMN

# Data ingestion Artifact 
path - networksecurity/entity/artifact_entity.py

using data class define the path to save o/p of data ingestion 
e.g @dataclass
class DataIngestionArtiface:


# Initiate Data ingestion
path - networksecurity/components/dataingestion.py

*************************************DATA VALIDATION****************************************************************

# DataValidation Constants decleration 
path - networksecurity/constant/training_pipeline/__init__.py 
a. Define the constants with their values used in Data validation

 