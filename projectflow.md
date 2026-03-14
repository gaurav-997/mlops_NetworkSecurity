#  MLOps practice: data drift, model drift, concept drift, monitoring, and automated retraining with safe deployment and rollback.
Data Ingestion → Validation (data drift) → Transformation → Training → 
Evaluation → Pusher → Prediction API → Monitoring (model/concept drift) → 
[Drift Alert] → Retraining Trigger → Training Pipeline → Safe Deployment → Rollback if needed


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

*************************************Model Pusher*************************************

# Model Pusher Constants
path - networksecurity/constant/training_pipeline/__init__.py
a. MODEL_PUSHER_DIR_NAME, SAVED_MODEL_DIR
b. TRAINING_BUCKET_NAME (cloud storage for production models)

# Model Pusher Config
path - networksecurity/entity/config_entity.py
ModelPusherConfig stores: model_pusher_dir, saved_model_dir, model_file_path

# Model Pusher Artifact
path - networksecurity/entity/artifact_entity.py
ModelPusherArtifact: is_pushed, model_dir, saved_model_path

# Model Pusher Component
path - networksecurity/components/modelpusher.py
Input: ModelEvaluationArtifact + ModelPusherConfig
1. Runs only when ModelEvaluationArtifact.is_model_accepted is True
2. Copies best model from final_model/ to saved_model/ (or pushes to S3/GCS using TRAINING_BUCKET_NAME)
3. Returns ModelPusherArtifact with paths for deployment

*************************************Model Tracking (MLflow + DVC + DagsHub)*************************************

# MLflow - Experiment & Model Registry
path - networksecurity/utils/main_utils/mlflow_utils.py or integrate in modeltraining.py
1. Set tracking URI (local mlruns/ or DagsHub remote)
2. mlflow.set_experiment("NetworkSecurity_Phishing")
3. In ModelTraining.initiate_model_training():
   - mlflow.start_run()
   - Log params: model_name, expected_accuracy, overfitting_threshold
   - Log metrics: train_f1, test_f1, precision, recall
   - Log model: mlflow.sklearn.log_model(best_model, "model")
   - mlflow.end_run()
4. Register best model to MLflow Model Registry (promote to "Production" when model accepted in evaluation)

# DVC - Data & Artifact Versioning
path - dvc.yaml, .dvc/config
1. dvc init
2. Track data: dvc add Network_data/phisingData.csv (add to .gitignore, push to remote)
3. Track artifacts: dvc add Artifacts/ (or stage-specific: transformed data, model.pkl)
4. Pipeline in dvc.yaml: data_ingestion → validation → transformation → training → evaluation
5. dvc repro to run pipeline; dvc push to sync with DagsHub/S3/GCS

# DagsHub - Unified MLOps Hub
1. Create repo on dagshub.com, connect GitHub
2. DagsHub = Git + DVC + MLflow in one place
3. Set MLflow tracking: export MLFLOW_TRACKING_URI=https://dagshub.com/<user>/<repo>.mlflow
4. DVC remote: dvc remote add origin https://dagshub.com/<user>/<repo>.git
5. Push experiments, models, data versions; view runs in DagsHub Experiments UI

# Integration Points
- modeltraining.py: wrap training loop with mlflow.start_run(), log metrics/model
- modelevaluation.py: log evaluation metrics, register model to registry if accepted
- training_pipeline.py: ensure DVC pipeline (dvc.yaml) matches orchestration order
- requirements.txt: mlflow, dvc, dagshub

*************************************Training Pipeline Orchestrator*************************************

# Training Pipeline
path - networksecurity/pipeline/training_pipeline.py
Orchestrates all components in sequence:
1. Init TrainingPipelineConfig, DataIngestionConfig, DataValidationConfig, DataTransformationConfig, ModelTrainerConfig, ModelEvaluationConfig, ModelPusherConfig

  self.training_pipeline_config = TrainingPipelineConfig()
2. DataIngestion.initiate_data_ingestion() → DataIngestionArtifact
3. DataValidation(artifact, config).initiate_data_validation() → DataValidationArtifact
4. DataTransformation(artifact, config).initiate_data_transformation() → DataTransformationArtifact
5. ModelTraining(artifact, config).initiate_model_training() → ModelTrainerArtifact
6. ModelEvaluation(trainer_artifact, transformation_artifact, config).initiate_model_evaluation() → ModelEvaluationArtifact
7. ModelPusher(eval_artifact, config).initiate_model_pusher() → ModelPusherArtifact (if model accepted)
8. sync_saved_model_dir_to_s3() → Uploads final_model/ to S3 (optional, if boto3 installed)
9. sync_artifact_dir_to_s3() → Uploads entire Artifacts/ directory to S3 (optional, if boto3 installed)
10. Log each stage, handle CustomException, stop pipeline on failure

# S3 Cloud Sync Functions
path - networksecurity/cloud/s3_syncer.py + networksecurity/pipeline/training_pipeline.py

## S3Sync Class
1. S3Sync.__init__() - Initializes boto3 S3 client and resource (requires AWS credentials)
2. sync_folder_to_s3(folder_path, bucket_name, s3_folder_name) - Uploads local folder to S3
3. sync_folder_from_s3(folder_path, bucket_name, s3_folder_name) - Downloads S3 folder to local

## TrainingPipeline S3 Methods
1. sync_artifact_dir_to_s3():
   - Uploads Artifacts/ to s3://bucket/artifacts/NetworkSecurity/YYYYMMDD_HHMMSS/
   - Backs up all pipeline outputs: data ingestion, validation, transformation, models, evaluations
   - Runs automatically after Model Pusher (if model accepted)
   - Gracefully skips if boto3 not installed

2. sync_saved_model_dir_to_s3():
   - Uploads final_model/ (model.pkl + preprocessor.pkl) to S3
   - Creates two versions:
     * Latest: s3://bucket/models/NetworkSecurity/latest/
     * Backup: s3://bucket/models/NetworkSecurity/backups/YYYYMMDD_HHMMSS/
   - Runs automatically after Model Pusher (if model accepted)
   - Gracefully skips if boto3 not installed

## AWS Setup Required
- Install: pip install boto3 s3fs
- Configure: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION (in .env or AWS CLI)
- Bucket: TRAINING_BUCKET_NAME = "netwworksecurity" (defined in constants)
- Permissions: s3:PutObject, s3:GetObject, s3:ListBucket
- See S3_SYNC_SETUP.md for detailed setup guide

*************************************Main Entry Point*************************************

# main.py
path - main.py (project root)
1. Import TrainingPipeline from networksecurity.pipeline.training_pipeline
2. Instantiate pipeline with configs
3. Call pipeline.run_pipeline()
4. Log success/failure
5. Can be run with: python main.py

*************************************Prediction / Serving*************************************

# Prediction Pipeline / API
path - app.py (FastAPI) + networksecurity/utils/ml_utils/model/estimator.py (NetworkModel wrapper)

## Implementation:
1. **Model & Preprocessor Loading:**
   - Load preprocessor from final_model/preprocessor.pkl using load_object()
   - Load trained model from final_model/model.pkl using load_object()
   - Wrap both in NetworkModel class for unified prediction interface

2. **NetworkModel Wrapper Class:**
   path - networksecurity/utils/ml_utils/model/estimator.py
   - Constructor: NetworkModel(preprocessor, model)
   - predict() method: applies preprocessing → model.predict() → returns predictions

3. **FastAPI Routes:**
   - GET / → RedirectResponse to /docs (auto API documentation)
   - GET /train → Instantiates TrainingPipeline, runs run_pipeline(), returns "Training is successful"
   - POST /predict → Accepts CSV file upload (UploadFile), loads models, predicts, returns HTML table

4. **Prediction Flow (POST /predict):**
   - Accept CSV file with URL features (30 columns, no target)
   - Read CSV into pandas DataFrame
   - Load preprocessor and model from final_model/
   - Create NetworkModel instance
   - Call network_model.predict(df) → applies preprocessing + prediction
   - Add predicted_column to DataFrame (1 = phishing, 0 = legitimate)
   - Save predictions to prediction_output/output.csv
   - Render predictions as Bootstrap HTML table using Jinja2 templates/table.html
   - Return interactive table with summary stats, color-coded results, CSV download button

5. **Tech Stack:**
   - FastAPI: Web framework with automatic OpenAPI docs
   - Uvicorn: ASGI server (run with app_run)
   - Jinja2Templates: HTML rendering for prediction results
   - CORS middleware: Allow cross-origin requests
   - Pandas: CSV processing
   - Local file storage: No MongoDB/Atlas (using local final_model/ and prediction_output/)

*************************************Model Drift Monitoring (Prometheus + Grafana)*************************************

# Prometheus - Metrics Collection
path - networksecurity/utils/main_utils/prometheus_utils.py, prediction API / inference service
1. Expose /metrics endpoint (prometheus_client library) in FastAPI/Flask app
2. Custom metrics to expose:
   - model_predictions_total (counter: total predictions)
   - model_prediction_latency_seconds (histogram: inference time)
   - model_prediction_class (counter: phishing vs legitimate counts)
   - model_drift_score (gauge: drift between production data vs training baseline, e.g. PSI/KS)
   - model_accuracy_rolling (gauge: rolling accuracy when ground truth available)
3. prometheus_client.start_http_server() or mount on existing app
4. Configure Prometheus to scrape /metrics at regular interval (e.g. every 15s)

# Grafana - Dashboards & Alerts
path - grafana/dashboards/ (JSON exports), docker-compose for Prometheus + Grafana
1. Connect Grafana to Prometheus as data source
2. Dashboards:
   - Prediction volume over time (model_predictions_total)
   - Latency distribution (model_prediction_latency_seconds)
   - Class distribution (phishing vs legitimate ratio over time)
   - Model drift score (alert when drift_score > threshold)
   - Rolling accuracy (when labeled feedback available)
3. Alerts: drift_score > 0.2, accuracy_drop > 10%, latency_p99 > 500ms
4. Notification channels: Slack, email, PagerDuty

# Drift Detection Logic
path - networksecurity/components/modelmonitoring.py or integrate in prediction pipeline
1. Data drift: compare feature distributions (PSI, KS test) of incoming requests vs training baseline
2. Model drift: track prediction distribution shift (class ratio change)
3. Concept drift: when ground truth available, compare predicted vs actual (accuracy drop)
4. Store baseline stats (mean, std, quantiles) at model deploy; compute drift periodically (batch or sliding window)
5. Export drift_score to Prometheus; Grafana alerts when threshold exceeded → trigger retrain

*************************************Model Retraining Trigger & Pipeline*************************************

# Retraining Triggers
path - CI/CD workflow, cron job, or event-driven (e.g. Airflow DAG)
1. Scheduled: run training pipeline daily/weekly (cron, GitHub Actions schedule)
2. Drift-based: when Grafana/Prometheus alert fires (drift_score > threshold) → trigger pipeline
3. Data-based: when new labeled data exceeds threshold (e.g. 1000 new samples) → trigger pipeline
4. Manual: on-demand run via CI/CD or python main.py

# Retraining Data Strategy
path - networksecurity/pipeline/retraining_config.py or constants
1. Full retrain: use all historical data (DVC-tracked) + new production data
2. Incremental: append feedback/ground-truth data to training set
3. Windowed: use last N days/months only (avoid stale data)
4. Version data with DVC before retrain; log data version in MLflow run

# Feedback Loop / Ground Truth Collection
path - networksecurity/components/feedback_collector.py, DB/table for feedback
1. Store user feedback (correct/incorrect) or delayed labels (e.g. reported phishing)
2. Log prediction + actual (when available) for concept drift & rolling accuracy
3. Export to DVC/S3 for inclusion in next retrain
4. Schema: request_id, features, prediction, actual_label, timestamp

*************************************Safe Deployment (A/B, Shadow, Rollback)*************************************

# Shadow Deployment
path - prediction API / load balancer config
1. Run new model in parallel; log its predictions but serve old model's response
2. Compare metrics (latency, predicted distribution) before promoting

# A/B or Canary Deployment
path - prediction API, feature flags (e.g. LaunchDarkly) or traffic split
1. Route 5–10% traffic to new model, 90–95% to current production
2. Compare accuracy, latency, error rate; promote if metrics pass

# Rollback Strategy
path - Model Registry (MLflow), deployment scripts
1. Keep previous production model version available (MLflow "Production" with version history)
2. On alert (accuracy drop, high error rate): auto or manual rollback to previous version
3. Document rollback runbook: kubectl/API config change to point to older model artifact

# Integration
- app.py / prediction_pipeline.py: add prometheus_client metrics, call drift logic per batch
- docker-compose.yml: prometheus, grafana, prediction-api services
- requirements.txt: prometheus_client

*************************************Docker & CI/CD (Essential for Production)*************************************

# Docker
- Dockerfile: build image with requirements, run main.py for training
- docker-compose: orchestrate prediction API, Prometheus, Grafana
- Build & push image to registry (Docker Hub, ECR, GCR)

# CI/CD Pipeline
- GitHub Actions / GitLab CI: trigger training on schedule, on data change, or on drift alert (webhook from Grafana)
- Workflow: checkout → install deps → run training pipeline → (optional) run tests
- On success: push model artifacts, update Model Registry, deploy (with shadow/canary if configured)
- On drift alert: webhook → trigger retraining workflow → evaluate → deploy if accepted

# Note
Optional for learning/prototyping (run python main.py manually). Essential for production: ensures repeatable builds, automated retraining, and reliable deployment.
