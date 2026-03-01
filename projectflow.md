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
need logging , exception , its config and artifacts 
split the data into train & test 

*************************************DATA VALIDATION****************************************************************

# DataValidation Constants decleration 
path - networksecurity/constant/training_pipeline/__init__.py 
a. Define the constants with their values used in Data validation
e.g data validation dir , valid dir , invalid data dir , drift report dir , drift report file , processing pkl file name 

# DataValidation congig and artifact decleration 

# define data schema.yaml file
path - data_schema\schema.yaml
this file has name of all columns names , target columns names , numerical columns names , categorical columns names 

# write common function like read yaml file and write data to yaml 
path - networksecurity\utils\main_utils\utils.py

# Data validation initiate 
here we will use scipy liberary ks_2samp module that will check 2 samples of data for decting data drift 
as usual input to datavalidation is data ingestion artifact and data validation config 

*****************************Datatransformation*********************************************
Here we will use KNN imputer ( KNN imputer is used to fetch missing data it uses average of 3 closest data points to predict 4th one )

1. update constants 
2. call these into config files 
3. update artifacts 



 