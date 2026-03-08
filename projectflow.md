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
4. write datatransformation.py

*************************************Model Training**************************************

# Model Training Constants
path - networksecurity/constant/training_pipeline/__init__.py
a. MODEL_TRAINER_DIR_NAME, MODEL_TRAINER_TRAINED_MODEL_DIR, MODEL_TRAINER_TRAINED_MODEL_NAME
b. MODEL_TRAINER_EXPECTED_SCORE (0.6) - minimum F1 score to accept a model
c. MODEL_TRAINER_OVER_FIITING_UNDER_FITTING_THRESHOLD (0.05) - max allowed train-test F1 diff

# Model Training Config
path - networksecurity/entity/config_entity.py
ModelTrainerConfig stores: model_trainer_dir, trained_model_file_path, expected_accuracy, overfitting_underfitting_threshold

# Model Training Artifact
path - networksecurity/entity/artifact_entity.py
ClassificationMetricArtifact: f1_score, precision_score, recall_score
ModelTrainerArtifact: trained_model_file_path, train_metric_artifact, test_metric_artifact

# Model Training Component
path - networksecurity/components/modeltraining.py
1. Loads transformed train/test numpy arrays (last column = target)
2. Trains 6 classifiers: Random Forest, Decision Tree, Gradient Boosting, Logistic Regression, AdaBoost, KNN
3. Selects the best model based on test F1 score
4. Validates best model exceeds expected_accuracy threshold (0.6)
5. Checks overfitting: rejects if train-test F1 diff > 0.05
6. Saves the best model as pickle and returns ModelTrainerArtifact with train/test metrics

*************************************Model Evaluation*************************************
Takes the already-trained best model and compares it against a previously saved production model to decide whether to promote the new model. This is model evaluation (is the new model good enough to deploy).


# Model Evaluation Constants
path - networksecurity/constant/training_pipeline/__init__.py
a. MODEL_EVALUATION_DIR_NAME, MODEL_EVALUATION_REPORT_NAME
b. MODEL_EVALUATION_CHANGED_THRESHOLD_SCORE (0.02) - min F1 improvement to accept new model
c. BEST_MODEL_DIR ("final_model"), BEST_MODEL_FILE_NAME ("model.pkl")

# Model Evaluation Config
path - networksecurity/entity/config_entity.py
ModelEvaluationConfig stores: model_evaluation_dir, report_file_path, change_threshold, best_model_dir, best_model_file_path

# Model Evaluation Artifact
path - networksecurity/entity/artifact_entity.py
ModelEvaluationArtifact: is_model_accepted, improved_accuracy, best_model_path, trained_model_path, train_metric_artifact, best_model_metric_artifact

# Model Evaluation Component
path - networksecurity/components/modelevaluation.py
Input: ModelTrainerArtifact + DataTransformationArtifact + ModelEvaluationConfig
1. Loads test data from transformed numpy arrays
2. Loads trained model from ModelTrainerArtifact and evaluates it (F1, precision, recall)
3. Checks if a previously saved best model exists at final_model/model.pkl
   - If no existing model: accepts the trained model and saves it as best model
   - If existing model found: compares F1 scores, accepts only if improvement > change_threshold (0.02)
4. Returns ModelEvaluationArtifact with is_model_accepted, improvement score, and metrics

 