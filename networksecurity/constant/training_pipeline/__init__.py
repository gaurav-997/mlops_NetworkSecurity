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

# data transformation 
DATA_TRANSFORMATION_DIR_NAME = "data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR = "transformed"
DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR = "transformed_object"
DATA_TRANSFORMATION_IMPUTER_PARAMS = {
    "missing_values": np.nan,
    "n_neighbors": 3,
    "weights": "uniform",
}
DATA_TRANSFORMATION_TRAIN_FILE_NAME = "train.py"
DATA_TRANSFORMATION_TEST_FILE_NAME = "test.py"


# ******************************Mode training *********************************

MODEL_TRAINER_DIR_NAME: str = "model_trainer"
MODEL_TRAINER_TRAINED_MODEL_DIR: str = "trained_model"
MODEL_TRAINER_TRAINED_MODEL_NAME: str = "model.pkl"
MODEL_TRAINER_EXPECTED_SCORE: float = 0.6
MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD: float = 0.05

# ******************************Model Evaluation *********************************

MODEL_EVALUATION_DIR_NAME: str = "model_evaluation"
MODEL_EVALUATION_CHANGED_THRESHOLD_SCORE: float = 0.02
MODEL_EVALUATION_REPORT_NAME: str = "report.yaml"
BEST_MODEL_DIR: str = "final_model"
BEST_MODEL_FILE_NAME: str = "model.pkl"

# *****************************Model Pusher************************************

MODEL_PUSHER_DIR_NAME: str = "final_model"
MODEL_PUSHER_MODEL_FILE_NAME: str = "model.pkl"

# AWS S3 Configuration
TRAINING_BUCKET_NAME = "networksecurity"  # Change this to your actual S3 bucket name