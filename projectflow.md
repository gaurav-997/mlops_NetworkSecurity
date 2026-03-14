#  MLOps Practice: Network Security Phishing Detection
**Complete Production-Ready Implementation**

## Project Overview
End-to-end MLOps pipeline for phishing URL detection with automated monitoring, drift detection, and retraining capabilities. Deployed on Kubernetes with enterprise-grade CI/CD.

## Architecture Flow
```
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

# *****************************Datatransformation*********************************************
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
#  I want to understand how training_pipeline is connected to app.py and how the model is being used in the predict route.
#  The app.py file serves as the main entry point for the application, where we define the FastAPI web server and its routes. The /train route triggers the training pipeline, which is defined in the training_pipeline module. This pipeline includes all the steps necessary to train the model, such as data ingestion, validation, transformation, model training, evaluation, and pushing. When the /train route is accessed, it initializes and runs the training pipeline, which ultimately results in a trained model being saved to a specified location.
#  The /predict route accepts a CSV file, processes it through the trained model, and returns the predictions in an HTML table format.
#  The NetworkModel class is used to wrap the preprocessing and prediction logic, allowing us to easily make predictions on new data.

# main.py
path - main.py (project root)
1. Import TrainingPipeline from networksecurity.pipeline.training_pipeline
2. Instantiate pipeline with configs
3. Call pipeline.run_pipeline()
4. Log success/failure
5. Can be run with: python main.py

*************************************Prediction / Serving using FastAPI*************************************

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
   - **GET /health** → Health check endpoint for Kubernetes liveness/readiness probes (returns model status)
   - GET /train → Instantiates TrainingPipeline, runs run_pipeline(), returns "Training is successful"
   - POST /predict → Accepts CSV file upload, loads models, predicts, returns HTML table with Prometheus metrics tracking
   - **GET /metrics** → Prometheus metrics endpoint (exposes 7 custom metrics)
   - **POST /feedback** → Submit ground truth feedback for predictions
   - **POST /webhook/retrain** → Webhook endpoint for Grafana/Alertmanager drift alerts
   - **POST /manual-retrain** → Manual retraining trigger
   - **GET /feedback-stats** → Statistics about collected feedback data

4. **Prediction Flow (POST /predict):**
   - Accept CSV file with URL features (30 columns, no target)
   - Read CSV into pandas DataFrame
   - Load preprocessor and model from final_model/
   - Create NetworkModel instance
   - Call network_model.predict(df) → applies preprocessing + prediction
   - **Track metrics:** predictions_total, latency, class distribution (Prometheus)
   - Add predicted_column to DataFrame (1 = phishing, 0 = legitimate)
   - Save predictions to prediction_output/output.csv
   - Render predictions as Bootstrap HTML table using Jinja2 templates/table.html
   - Return interactive table with summary stats, color-coded results, CSV download button

5. **Tech Stack:**
   - FastAPI: Web framework with automatic OpenAPI docs
   - Uvicorn: ASGI server (run with app_run or in Docker)
   - Jinja2Templates: HTML rendering for prediction results
   - CORS middleware: Allow cross-origin requests
   - Pandas: CSV processing
   - Prometheus Client: Metrics collection and export
   - Local file storage: No MongoDB/Atlas (using local final_model/ and prediction_output/)

*************************************Model Drift Monitoring (Prometheus + Grafana)*************************************

# Prometheus - Metrics Collection
path - networksecurity/utils/main_utils/prometheus_utils.py, app.py
1. Expose /metrics endpoint (prometheus_client library) in FastAPI app
2. Custom metrics exposed (7 metrics total):
   - **model_predictions_total** (Counter: total predictions by model version and endpoint)
   - **model_prediction_latency_seconds** (Histogram: inference time distribution)
   - **model_class_predictions** (Counter: phishing vs legitimate counts)
   - **model_drift_score** (Gauge: drift between production data vs training baseline, using PSI/KS)
   - **model_rolling_accuracy** (Gauge: rolling accuracy when ground truth available)
   - **model_errors_total** (Counter: error tracking by error type)
   - **data_quality_score** (Gauge: data quality metrics)
3. Integration with prediction flow: automatically tracks metrics on each /predict request
4. **Kubernetes Integration:** ServiceMonitor auto-discovers /metrics endpoint (no manual scrape config needed)

# Grafana - Dashboards & Alerts (Kubernetes Deployment)
path - k8s/servicemonitor.yaml (Prometheus Operator integration)
1. **Prometheus Operator Stack** (installed via Helm):
   - Prometheus for metrics collection
   - Grafana for visualization
   - Alertmanager for notifications
   - Auto-discovery via ServiceMonitor CRD
   
2. **ServiceMonitor Configuration:**
   - Automatically discovers network-security-api service
   - Scrapes /metrics endpoint every 15 seconds
   - No manual prometheus.yml configuration needed
   
3. **PrometheusRule - 8 Alert Rules:**
   - HighErrorRate: rate > 0.05 errors/sec for 5m
   - HighPredictionLatency: P99 > 1.0s for 5m
   - DataDriftDetected: drift_score > 0.5 for 10m (CRITICAL - triggers retraining)
   - ModelAccuracyDrop: rolling_accuracy < 0.70 for 15m (CRITICAL - triggers retraining)
   - APIDown: service unreachable for 2m
   - HighPodRestartRate: frequent pod restarts
   - HighCPUUsage: container CPU > 1.5 cores for 10m
   - HighMemoryUsage: memory > 90% limit for 10m
   
4. **Dashboards:**
   - Prediction volume over time (model_predictions_total)
   - Latency distribution (p50, p95, p99)
   - Class distribution (phishing vs legitimate ratio)
   - Model drift score timeline (alert when > threshold)
   - Rolling accuracy (when labeled feedback available)
   - Error rates by type
   - Resource utilization (CPU, memory)
   
5. **Notification channels:** Slack webhooks (configured in AlertManager)

# Drift Detection Logic
path - networksecurity/components/modelmonitoring.py
1. **ModelMonitor Class** with three drift detection methods:
   - **Data drift:** PSI (Population Stability Index), KS test, JS divergence
   - **Model drift:** Prediction distribution shift detection
   - **Concept drift:** Accuracy drop detection (when ground truth available)
   
2. **Implementation:**
   - Store baseline statistics (mean, std, quantiles) at model deployment
   - Compare incoming requests vs training baseline
   - Compute drift_score periodically (batch or sliding window)
   - Export drift_score to Prometheus via model_drift_score gauge
   - Grafana alerts when drift_score > 0.5 → webhook triggers retraining
   
3. **Baseline Management:**
   - create_baseline() from training data
   - save_baseline() to baseline_stats/ directory
   - load_baseline() for production monitoring
   - generate_drift_report() creates JSON reports

# Access Monitoring (Kubernetes)
```bash
# Install Prometheus Operator
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Deploy ServiceMonitor
kubectl apply -f k8s/servicemonitor.yaml

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Login: admin / admin
```

*************************************Docker & Kubernetes (Production Deployment)*************************************

# Docker
- **Dockerfile** (Multi-stage build for optimization):
  - Builder stage: Install dependencies in isolated layer
  - Runtime stage: Production image with non-root user (security)
  - Multi-mode support via docker-entrypoint.sh
  - Health check: curl /health endpoint
  - Optimized with .dockerignore

- **docker-entrypoint.sh** (Flexible container startup):
  - Mode 'api': Run FastAPI prediction service (uvicorn)
  - Mode 'train': Execute training pipeline (python main.py)
  - Mode 'test': Run pytest test suite
  - Mode 'retrain': Run scheduled retraining script
  - Mode 'bash': Interactive shell for debugging

- **Build & Push:**
  - Build: `docker build -t network-security:latest .`
  - Multi-registry support: Docker Hub, AWS ECR, Google GCR
  - Automated via GitHub Actions CI/CD

# Kubernetes Deployment (Production-Ready)
**Note:** Replaced Docker Compose with Kubernetes for production scalability and reliability

## Kubernetes Manifests (k8s/ directory - 13 files)
1. **namespace.yaml** - Isolated network-security namespace
2. **configmap.yaml** - Application configuration (env vars, feature flags)
3. **secret.yaml** - Sensitive credentials (AWS keys, Slack webhooks, DB passwords)
4. **serviceaccount.yaml** - IRSA for AWS access (no hardcoded credentials)
5. **deployment.yaml** - API deployment:
   - 3 replicas (high availability)
   - Health probes: liveness (/health), readiness (/health), startup (/health)
   - Resource limits: CPU 2 cores, Memory 4Gi
   - Rolling update strategy (zero downtime)
   - Pod anti-affinity (spread across nodes)
6. **service.yaml** - ClusterIP service exposing port 8000
7. **ingress.yaml** - AWS ALB integration:
   - SSL/TLS termination
   - Health check configuration
   - ACM certificate support
   - WAF integration (optional)
8. **hpa.yaml** - Horizontal Pod Autoscaler:
   - Min 3 pods, Max 20 pods
   - CPU threshold: 70%, Memory: 80%
   - Custom metrics: request rate, prediction latency
   - Smart scaling behavior (fast scale-up, slow scale-down)
9. **pvc.yaml** - Persistent Volume Claims:
   - model-data-pvc: 10Gi (ReadWriteMany for multi-pod access)
   - feedback-data-pvc: 5Gi (SQLite database)
   - training-data-pvc: 20Gi (DVC data storage)
   - AWS EFS StorageClass for shared storage
10. **redis.yaml** - Redis deployment for API caching (1 replica, 512Mi memory)
11. **cronjob.yaml** - Scheduled training job:
    - Runs every Sunday at 2 AM UTC
    - Pulls data with DVC, trains model, pushes to S3
    - Resource allocation: 4 CPU, 16Gi memory
12. **servicemonitor.yaml** - Prometheus Operator integration:
    - ServiceMonitor CRD for auto-discovery
    - PrometheusRule with 8 alert definitions
13. **kustomization.yaml** - Kustomize for environment overlays (staging/production)

## Helm Chart (helm/network-security/ directory)
Production-grade Helm chart with templating:
- **Chart.yaml** - Metadata and dependencies
- **values.yaml** - Default configuration (3 replicas, 1Gi memory)
- **values-staging.yaml** - Staging overrides (2 replicas, smaller resources)
- **values-production.yaml** - Production overrides (5 replicas, larger resources, dedicated nodes)
- **templates/** - 9 templated Kubernetes resources:
  - deployment.yaml, service.yaml, configmap.yaml, secret.yaml
  - hpa.yaml, ingress.yaml, serviceaccount.yaml, pvc.yaml
  - _helpers.tpl (template functions)

## Deployment Commands
```bash
# Using Helm (Recommended)
helm install network-security ./helm/network-security \
  --namespace network-security \
  --create-namespace \
  --values ./helm/network-security/values-production.yaml

# Using Kustomize
kubectl apply -k k8s/

# Using raw manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
# ... (apply all files)
```

## Key Features
- **Auto-scaling:** HPA scales 3-20 pods based on CPU/Memory/custom metrics
- **High Availability:** Multi-AZ deployment, pod anti-affinity, health probes
- **Security:** Non-root containers, IRSA, network policies, secret management
- **Monitoring:** ServiceMonitor auto-discovers /metrics, PrometheusRule alerts
- **Zero Downtime:** Rolling updates, readiness probes prevent traffic to unhealthy pods
- **Resource Management:** Requests/limits prevent resource starvation
- **Scheduled Training:** CronJob runs weekly training automatically

# CI/CD Pipeline (GitHub Actions - 4 Workflows)

## 1. CI Workflow (.github/workflows/ci.yaml)
**Triggers:** Push to main/develop, pull requests
**6 Jobs:**
- Code Quality: Black, isort, Flake8, Pylint
- Unit Tests: pytest with coverage reports
- Security Scan: Safety (dependencies), Bandit (code)
- Docker Build: Multi-stage build test
- Integration Tests: API endpoint testing
- CI Summary: Aggregate results, fail on critical issues

## 2. CD Workflow (.github/workflows/cd.yaml)
**Triggers:** Push to main, tags (v*.*.*), manual dispatch
**4 Jobs:**
- **Build & Push:** Multi-registry Docker image push (Docker Hub, ECR, GCR)
- **Deploy Staging (Kubernetes):**
  - Configure kubectl for EKS staging cluster
  - Helm upgrade --install with values-staging.yaml
  - Wait for rollout completion
  - Health check verification
  - Smoke tests
- **Deploy Production (Kubernetes):**
  - Three deployment strategies (workflow input):
    - **Rolling:** Standard rolling update (default)
    - **Canary:** 10% traffic to new version, monitor before promotion
    - **Blue-Green:** Deploy to green, switch traffic, keep blue for rollback
  - Helm upgrade --install with values-production.yaml
  - Production smoke tests
  - Slack notification on success/failure
- **Rollback:** Manual trigger to revert to previous Helm release

## 3. Training Pipeline Workflow (.github/workflows/training_pipeline.yaml)
**Triggers:** Schedule (weekly), manual, webhook (drift alert), data changes
**4 Jobs:**
- **Check Training Conditions:**
  - Manual trigger, drift alert, scheduled run
  - Check feedback data thresholds
  - DVC pull latest data
- **Run Training:**
  - Execute python main.py (full training pipeline)
  - MLflow experiment tracking
  - Model validation tests
  - DVC push artifacts
  - Update MLflow Model Registry
- **Evaluate Model:**
  - Compare new vs production model
  - Check acceptance criteria (accuracy > 75%, F1 > 70%)
  - Generate evaluation report
- **Deploy Model (if approved):**
  - Upload to S3 (versioned)
  - Trigger CD pipeline for API deployment
  - Slack notification

## 4. Model Retraining Workflow (.github/workflows/model_retraining.yml)
**Triggers:** Schedule (Sunday 2 AM), webhook (drift alert), manual
**Similar to Training Pipeline but with:**
- Retraining-specific data preparation (feedback loop integration)
- Incremental/windowed retraining strategies
- Automated deployment approval based on metrics

## Webhook Integration
- Grafana/Alertmanager → POST /webhook/retrain endpoint
- On drift alert (model_drift_score > 0.5) → Trigger training pipeline
- Automated end-to-end: drift detection → retraining → model evaluation → deployment

## Secrets Required (GitHub Secrets)
- AWS: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
- Docker: DOCKER_USERNAME, DOCKER_PASSWORD
- Kubernetes: EKS cluster kubeconfig (via AWS credentials)
- MLflow: MLFLOW_TRACKING_URI, MLFLOW_TRACKING_USERNAME, MLFLOW_TRACKING_PASSWORD
- Notifications: SLACK_WEBHOOK_URL
- Model Registry: MODEL_BUCKET, TRAINING_BUCKET_NAME

# Documentation
- **K8S_DEPLOYMENT.md** (500+ lines): Complete Kubernetes deployment guide
- **QUICKSTART_K8S.md**: Quick command reference for common operations
- **IMPLEMENTATION_REVIEW.md**: Full implementation status and checklist

# Note
Kubernetes deployment is **production-ready** and provides:
- Automated scaling and self-healing
- Zero-downtime deployments with rollback
- Enterprise-grade monitoring and alerting
- Security best practices (IRSA, non-root, secrets)
- Multi-environment support (staging, production)
- CI/CD automation with multiple deployment strategies

*************************************Model Retraining Trigger & Pipeline*************************************

# Retraining Triggers (4 Types)
path - CI/CD workflows, scheduled_retrain.py, app.py webhooks

## 1. Scheduled Retraining
- **Kubernetes CronJob** (k8s/cronjob.yaml): Runs every Sunday at 2 AM UTC
- **GitHub Actions** (.github/workflows/training_pipeline.yaml): Weekly scheduled workflow
- **Cron/Task Scheduler** with scheduled_retrain.py script
- Use case: Regular model refresh regardless of drift

## 2. Drift-Based Retraining (Automated)
- **Trigger:** Grafana/Prometheus alert fires when drift_score > 0.5 or accuracy < 0.70
- **Flow:** PrometheusRule → Alertmanager → Webhook → POST /webhook/retrain → GitHub Actions repository_dispatch
- **Alertmanager Configuration:** Routes critical alerts to webhook endpoint
- **Implementation:** app.py /webhook/retrain endpoint receives alert payload, spawns retraining thread
- Use case: Automatic response to data/model/concept drift

## 3. Data-Based Retraining (Feedback Threshold)
- **Trigger:** When new labeled feedback data exceeds threshold (e.g., 1000 samples)
- **Check:** FeedbackCollector.should_trigger_retraining() method
- **Thresholds:** 
  - min_retraining_samples: 100 labeled samples minimum
  - accuracy_drop_threshold: 5% accuracy decline
- **Implementation:** Checked by scheduled_retrain.py or manual API call
- Use case: Incorporate production feedback into model

## 4. Manual Retraining (On-Demand)
- **API Endpoint:** POST /manual-retrain (app.py)
- **CLI Script:** python scheduled_retrain.py --strategy full --force
- **GitHub Actions:** Manual workflow_dispatch trigger
- **Use case:** Emergency retraining, testing, post-incident response

# Retraining Data Strategy
path - networksecurity/pipeline/retraining_config.py

## RetrainingStrategy Enum (3 Options)
1. **FULL:** Use all historical data (DVC-tracked) + new production feedback
   - Most accurate but slowest
   - Recommended for major model updates
   
2. **INCREMENTAL:** Append feedback/ground-truth data to existing training set
   - Faster than full retrain
   - Good for continuous learning
   - Risk of data imbalance over time
   
3. **WINDOWED:** Use last N days/months only (e.g., last 90 days)
   - Prevents stale data from affecting model
   - Handles concept drift better
   - Configurable window size

## RetrainingConfig Class
**Configuration options:**
- strategy: RetrainingStrategy (FULL/INCREMENTAL/WINDOWED)
- window_days: 90 (for WINDOWED strategy)
- min_retraining_samples: 100 (minimum labeled data required)
- accuracy_drop_threshold: 0.05 (5% accuracy decline triggers retrain)
- drift_score_threshold: 0.2 (PSI threshold for drift detection)
- use_dvc: True (version data with DVC before retraining)
- use_mlflow: True (log retraining run to MLflow)

## RetrainingManager Class
**Key methods:**
- **prepare_retraining_data():** Loads feedback, applies strategy, prepares training dataset
- **trigger_retraining():** Orchestrates full retraining pipeline with notifications
- **_version_data_with_dvc():** Versions training data using DVC, commits .dvc file
- **_send_notification():** Sends Slack notification on completion/failure

# Feedback Loop / Ground Truth Collection
path - networksecurity/components/feedback_collector.py

## FeedbackCollector Class (SQLite-based)
**Database Schema:**
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    request_id TEXT UNIQUE,
    timestamp DATETIME,
    prediction INTEGER,
    actual_label INTEGER,
    model_version TEXT,
    features TEXT (JSON),
    user_feedback TEXT,
    created_at DATETIME,
    updated_at DATETIME
)
```

**Key Methods:**
1. **store_prediction():** Save prediction request with features and model version
2. **update_ground_truth():** Update with actual label when available (e.g., user reports phishing)
3. **get_labeled_data():** Retrieve all predictions with ground truth for retraining
4. **export_for_retraining():** Export labeled data to CSV for training pipeline
5. **should_trigger_retraining():** Check if thresholds met (sample count, accuracy drop)
6. **get_statistics():** Return feedback stats (total, labeled, accuracy)

**Storage:** feedback_data/feedback.db (SQLite)

## API Integration (app.py)
**POST /feedback endpoint:**
- Request: `{"request_id": "abc123", "actual_label": 1, "user_feedback": "correct"}`
- Updates ground truth in feedback database
- Checks if retraining should be triggered
- Returns: `{"status": "success", "should_retrain": false}`

**GET /feedback-stats endpoint:**
- Returns collected feedback statistics
- Response: `{"total_records": 1500, "labeled_records": 800, "rolling_accuracy": 0.87, "last_updated": "2026-03-14T10:30:00"}`

# Retraining Execution Flow

## 1. Condition Check (scheduled_retrain.py or GitHub Actions)
```python
# Check if retraining needed
conditions = {
    "manual_trigger": is_manual,
    "drift_detected": drift_score > threshold,
    "data_threshold": labeled_samples >= min_samples,
    "accuracy_drop": current_accuracy < (baseline_accuracy - threshold)
}
should_retrain = any(conditions.values())
```

## 2. Data Preparation (RetrainingManager)
```python
# Load feedback data
feedback_data = feedback_collector.get_labeled_data()

# Apply strategy (FULL/INCREMENTAL/WINDOWED)
training_data = retraining_manager.prepare_retraining_data(
    feedback_data=feedback_data,
    strategy=RetrainingStrategy.INCREMENTAL
)

# Version with DVC
dvc add training_data.csv
git add training_data.csv.dvc
git commit -m "Version retraining data"
```

## 3. Training Execution (TrainingPipeline)
```python
# Run full training pipeline
training_pipeline = TrainingPipeline()
training_pipeline.run_pipeline()

# MLflow tracking
mlflow.log_param("retraining_reason", "drift_detected")
mlflow.log_param("data_strategy", "INCREMENTAL")
mlflow.log_metric("training_samples", len(training_data))
```

## 4. Model Evaluation (ModelEvaluation)
```python
# Compare new model vs production model
improvement = new_f1_score - production_f1_score

if improvement > change_threshold:
    accept_model = True
    # Push to final_model/ and S3
else:
    accept_model = False
    # Keep existing production model
```

## 5. Deployment (if accepted)
```python
# Push model to S3
sync_saved_model_dir_to_s3()

# Trigger CD pipeline
trigger_github_actions_workflow("cd.yaml")

# Or manual deployment
kubectl rollout restart deployment/network-security -n network-security
```

## 6. Notification (Slack)
```python
message = f"""
✅ Retraining Completed
Reason: {reason}
Strategy: {strategy}
Accuracy: {new_accuracy:.3f} (improvement: +{improvement:.3f})
Model accepted: {is_accepted}
Deployed: {deployed_timestamp}
"""
send_slack_notification(message)
```

# Scheduled Retraining Script
path - scheduled_retrain.py

## CLI Usage
```bash
# Full retrain (all data)
python scheduled_retrain.py --strategy full

# Incremental retrain (append new data)
python scheduled_retrain.py --strategy incremental

# Windowed retrain (last 90 days)
python scheduled_retrain.py --strategy windowed

# Check if retraining needed (dry run)
python scheduled_retrain.py --check-only

# Force retrain regardless of conditions
python scheduled_retrain.py --force --strategy full
```

## Cron Configuration
```bash
# Edit crontab
crontab -e

# Add weekly retraining (Sunday 2 AM)
0 2 * * 0 cd /path/to/project && /path/to/venv/bin/python scheduled_retrain.py --strategy incremental >> logs/retrain.log 2>&1

# Add daily drift check
0 */6 * * * cd /path/to/project && /path/to/venv/bin/python scheduled_retrain.py --check-only >> logs/retrain_check.log 2>&1
```

# DVC Integration for Retraining
**Before each retrain:**
```bash
# Version current training data
dvc add Network_data/training_data.csv
git add Network_data/training_data.csv.dvc
git commit -m "chore: version training data before retrain-$(date +%Y%m%d)"
dvc push
```

**After retrain:**
```bash
# Version new model artifacts
dvc add final_model/
git add final_model.dvc
git commit -m "feat: model retrained with strategy=INCREMENTAL"
dvc push
```

# MLflow Tracking for Retraining
**Logged parameters:**
- retraining_reason (drift/scheduled/manual/data_threshold)
- retraining_strategy (FULL/INCREMENTAL/WINDOWED)
- feedback_samples_count
- training_data_version (DVC commit hash)
- previous_model_version

**Logged metrics:**
- new_model_f1_score
- improvement_over_production
- training_time_seconds
- data_drift_score
- model_drift_score

# Production Monitoring & Alerts
**Alert triggers retraining automatically:**
1. PrometheusRule fires: model_drift_score > 0.5
2. Alertmanager routes to webhook: /webhook/retrain
3. FastAPI spawns background thread: RetrainingManager.trigger_retraining()
4. Training pipeline executes: Data prep → Train → Evaluate → Deploy
5. Slack notification sent: Success/Failure with metrics
6. Drift score resets after model deployment


