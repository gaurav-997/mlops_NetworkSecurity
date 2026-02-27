# common constants
TARGET_COLUMN= 'Result'
ARTIFACT_DIR_NAME = 'Artifacts'
PIPELINE_NAME = 'NetworkSecurity'
DATA_FILE_NAME = 'phisingData.csv'
TRAIN_FILE_NAME = 'train.csv'
TEST_FILE_NAME = 'test.csv'

SCHEMA_FILE_PATH = 'data_schema/schema.yaml'


# data ingestion constants 
DATA_INGESTION_DIR_NAME = 'data_ingestion'
DATA_INGESTION_FEATURE_STORE = 'feature_store'
DATA_INGESTION_INGESTED_DIR = 'ingested'
DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO = 0.2

# data validation constants 
DATA_VALIDATION_DIR_NAME = "data_validation"
DATA_VALIDATION_VALID_DIR = "validated"
DATA_VALIDATION_INVALID_DIR = 'invalid'
DATA_VALIDATION_DRIFT_REPORT_DIR = 'drift_report'
DATA_VALIDATION_DRIFT_REPORT_FILE_NAME = 'report.yaml'
DATA_VALIDATION_PREPROCESSING_OBJECT_FILE_NAME = "preprocessing.pkl"