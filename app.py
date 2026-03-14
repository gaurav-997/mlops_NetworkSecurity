import sys
import os
import pandas as pd
import time

from networksecurity.exception.exception import CustomException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse

from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel

# Import Prometheus metrics utilities
from networksecurity.utils.main_utils.prometheus_utils import (
    metrics_endpoint,
    model_predictions_total,
    model_prediction_latency_seconds,
    record_batch_predictions,
    model_errors_total
)

# Import feedback and retraining utilities
from networksecurity.components.feedback_collector import FeedbackCollector
from networksecurity.pipeline.retraining_config import (
    RetrainingManager,
    RetrainingConfig,
    RetrainingTrigger
)

# Initialize managers
feedback_collector = FeedbackCollector()
retraining_manager = RetrainingManager()

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="./templates")

@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and Docker healthchecks.
    Returns the health status of the API and its dependencies.
    """
    try:
        # Check if model files exist
        model_exists = os.path.exists("final_model/model.pkl")
        preprocessor_exists = os.path.exists("final_model/preprocessor.pkl")
        
        health_status = {
            "status": "healthy",
            "model_loaded": model_exists,
            "preprocessor_loaded": preprocessor_exists,
            "timestamp": time.time()
        }
        
        # If critical components are missing, return unhealthy
        if not model_exists or not preprocessor_exists:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes metrics for monitoring predictions, latency, drift, and accuracy.
    """
    return metrics_endpoint()

@app.get("/train")
async def train_route():
    try:
        train_pipeline = TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("Training is successful")
    except Exception as e:
        raise CustomException(e, sys)

@app.post("/predict")
async def predict_route(request: Request, file: UploadFile = File(...)):
    """
    Prediction endpoint with Prometheus metrics tracking.
    Accepts CSV file, makes predictions, and tracks metrics.
    """
    start_time = time.time()
    model_version = "v1.0"
    
    try:
        df = pd.read_csv(file.file)
        
        # Load preprocessor and model
        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")
        
        # Create network model
        network_model = NetworkModel(preprocessor=preprocessor, model=final_model)
        
        print(df.iloc[0])
        y_pred = network_model.predict(df)
        print(y_pred)
        
        df['predicted_column'] = y_pred
        print(df['predicted_column'])
        
        # Replace -1 with 0 for better readability
        df['predicted_column'].replace(-1, 0, inplace=True)
        
        # Save predictions to output directory
        os.makedirs('prediction_output', exist_ok=True)
        df.to_csv('prediction_output/output.csv', index=False)
        
        # ==================== Prometheus Metrics Tracking ====================
        
        # Record total predictions
        model_predictions_total.labels(
            model_version=model_version,
            endpoint="/predict"
        ).inc(len(df))
        
        # Record prediction latency
        latency = time.time() - start_time
        model_prediction_latency_seconds.labels(
            model_version=model_version,
            endpoint="/predict"
        ).observe(latency)
        
        # Record prediction classes (phishing vs legitimate)
        predictions_list = df['predicted_column'].tolist()
        record_batch_predictions(predictions_list, model_version)
        
        logging.info(f"Predictions completed: {len(df)} samples in {latency:.3f}s")
        
        # ======================================================================
        
        # Convert dataframe to HTML table
        table_html = df.to_html(classes='table table-striped')
        
        return templates.TemplateResponse("table.html", {"request": request, "table": table_html})
        
    except Exception as e:
        # Track errors in Prometheus
        model_errors_total.labels(
            error_type=type(e).__name__,
            model_version=model_version
        ).inc()
        
        logging.error(f"Prediction error: {str(e)}")
        raise CustomException(e, sys)

@app.post("/feedback")
async def submit_feedback(
    request_id: str,
    actual_label: int,
    user_feedback: str = None
):
    """
    Submit ground truth feedback for a prediction.
    
    Args:
        request_id: ID of the prediction request
        actual_label: Actual ground truth label (0 or 1)
        user_feedback: Optional user feedback ('correct' or 'incorrect')
    """
    try:
        feedback_collector.update_ground_truth(
            request_id=request_id,
            actual_label=actual_label,
            user_feedback=user_feedback
        )
        
        # Check if retraining should be triggered
        should_retrain, reason = feedback_collector.should_trigger_retraining()
        
        response_data = {
            "status": "success",
            "message": "Feedback recorded successfully",
            "request_id": request_id,
            "should_retrain": should_retrain,
            "reason": reason if should_retrain else None
        }
        
        return response_data
        
    except Exception as e:
        logging.error(f"Feedback submission error: {str(e)}")
        raise CustomException(e, sys)

@app.post("/webhook/retrain")
async def retrain_webhook(alert_data: dict = None):
    """
    Webhook endpoint for triggering retraining from Prometheus/Grafana alerts.
    
    Expected payload from Alertmanager:
    {
        "status": "firing",
        "alerts": [{
            "labels": {"alertname": "HighDataDrift"},
            "annotations": {"description": "..."}
        }]
    }
    """
    try:
        logging.info(f"Retraining webhook triggered: {alert_data}")
        
        # Determine trigger reason
        reason = "Webhook trigger"
        if alert_data and 'alerts' in alert_data:
            alerts = alert_data['alerts']
            if alerts:
                alert_name = alerts[0].get('labels', {}).get('alertname', 'Unknown')
                description = alerts[0].get('annotations', {}).get('description', '')
                reason = f"{alert_name}: {description}"
        
        # Trigger retraining in background (async)
        import threading
        
        def run_retraining():
            try:
                retraining_manager.trigger_retraining(
                    trigger_type=RetrainingTrigger.DRIFT_BASED,
                    reason=reason
                )
            except Exception as e:
                logging.error(f"Background retraining failed: {str(e)}")
        
        # Start retraining in background thread
        thread = threading.Thread(target=run_retraining)
        thread.start()
        
        return {
            "status": "accepted",
            "message": "Retraining triggered",
            "reason": reason
        }
        
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/manual-retrain")
async def manual_retrain():
    """
    Manual endpoint to trigger retraining on-demand.
    """
    try:
        logging.info("Manual retraining triggered")
        
        # Check if we have enough data
        stats = feedback_collector.get_statistics()
        
        if stats['labeled_records'] < 100:
            return {
                "status": "insufficient_data",
                "message": f"Only {stats['labeled_records']} labeled samples available (minimum: 100)",
                "stats": stats
            }
        
        # Trigger retraining in background
        import threading
        
        def run_retraining():
            try:
                retraining_manager.trigger_retraining(
                    trigger_type=RetrainingTrigger.MANUAL,
                    reason="Manual trigger via API"
                )
            except Exception as e:
                logging.error(f"Manual retraining failed: {str(e)}")
        
        thread = threading.Thread(target=run_retraining)
        thread.start()
        
        return {
            "status": "triggered",
            "message": "Retraining started in background",
            "stats": stats
        }
        
    except Exception as e:
        logging.error(f"Manual retrain error: {str(e)}")
        raise CustomException(e, sys)

@app.get("/feedback-stats")
async def get_feedback_stats():
    """
    Get statistics about feedback data.
    """
    try:
        stats = feedback_collector.get_statistics()
        return stats
    except Exception as e:
        logging.error(f"Error getting feedback stats: {str(e)}")
        raise CustomException(e, sys)

if __name__ == "__main__":
    app_run(app, host="0.0.0.0", port=8000)
