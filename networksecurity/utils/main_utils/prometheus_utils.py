"""
Prometheus Metrics Collection for Model Monitoring
Exposes custom metrics for tracking predictions, latency, drift, and accuracy.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from functools import wraps
import numpy as np
from scipy import stats
from typing import Dict, List, Optional
import logging

# ========================== Prometheus Metrics ==========================

# Counter: Total number of predictions made
model_predictions_total = Counter(
    'model_predictions_total',
    'Total number of predictions made by the model',
    ['model_version', 'endpoint']
)

# Counter: Predictions by class (phishing vs legitimate)
model_prediction_class = Counter(
    'model_prediction_class',
    'Count of predictions by class',
    ['class_label', 'model_version']
)

# Histogram: Prediction latency in seconds
model_prediction_latency_seconds = Histogram(
    'model_prediction_latency_seconds',
    'Time taken for model prediction in seconds',
    ['model_version', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Gauge: Model drift score (PSI/KS test statistic)
model_drift_score = Gauge(
    'model_drift_score',
    'Data drift score between production and training data',
    ['feature_name', 'drift_type']
)

# Gauge: Rolling accuracy when ground truth is available
model_accuracy_rolling = Gauge(
    'model_accuracy_rolling',
    'Rolling accuracy over recent predictions with ground truth',
    ['window_size', 'model_version']
)

# Gauge: Current number of predictions in rolling window
model_predictions_in_window = Gauge(
    'model_predictions_in_window',
    'Number of predictions in the current rolling window',
    ['window_size']
)

# Counter: Model errors
model_errors_total = Counter(
    'model_errors_total',
    'Total number of model prediction errors',
    ['error_type', 'model_version']
)


# ========================== Decorator for Tracking ==========================

def track_predictions(model_version: str = "v1.0", endpoint: str = "predict"):
    """
    Decorator to track prediction metrics automatically.
    
    Args:
        model_version: Version of the model being used
        endpoint: API endpoint name
        
    Usage:
        @track_predictions(model_version="v1.0", endpoint="/predict")
        def predict_function():
            # your prediction code
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute the prediction function
                result = await func(*args, **kwargs)
                
                # Track successful prediction
                model_predictions_total.labels(
                    model_version=model_version,
                    endpoint=endpoint
                ).inc()
                
                # Track latency
                latency = time.time() - start_time
                model_prediction_latency_seconds.labels(
                    model_version=model_version,
                    endpoint=endpoint
                ).observe(latency)
                
                return result
                
            except Exception as e:
                # Track errors
                model_errors_total.labels(
                    error_type=type(e).__name__,
                    model_version=model_version
                ).inc()
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute the prediction function
                result = func(*args, **kwargs)
                
                # Track successful prediction
                model_predictions_total.labels(
                    model_version=model_version,
                    endpoint=endpoint
                ).inc()
                
                # Track latency
                latency = time.time() - start_time
                model_prediction_latency_seconds.labels(
                    model_version=model_version,
                    endpoint=endpoint
                ).observe(latency)
                
                return result
                
            except Exception as e:
                # Track errors
                model_errors_total.labels(
                    error_type=type(e).__name__,
                    model_version=model_version
                ).inc()
                raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


# ========================== Metrics Recording Functions ==========================

def record_prediction_class(prediction: int, model_version: str = "v1.0"):
    """
    Record the predicted class (phishing or legitimate).
    
    Args:
        prediction: Predicted class (1 for phishing, 0 for legitimate)
        model_version: Version of the model
    """
    class_label = "phishing" if prediction == 1 else "legitimate"
    model_prediction_class.labels(
        class_label=class_label,
        model_version=model_version
    ).inc()


def record_batch_predictions(predictions: List[int], model_version: str = "v1.0"):
    """
    Record multiple predictions at once.
    
    Args:
        predictions: List of predicted classes
        model_version: Version of the model
    """
    for pred in predictions:
        record_prediction_class(pred, model_version)


def update_drift_score(feature_name: str, drift_score: float, drift_type: str = "psi"):
    """
    Update the drift score for a specific feature.
    
    Args:
        feature_name: Name of the feature being monitored
        drift_score: Calculated drift score (PSI, KS statistic, etc.)
        drift_type: Type of drift metric (psi, ks, js, etc.)
    """
    model_drift_score.labels(
        feature_name=feature_name,
        drift_type=drift_type
    ).set(drift_score)


def update_rolling_accuracy(accuracy: float, window_size: int = 100, model_version: str = "v1.0"):
    """
    Update the rolling accuracy metric.
    
    Args:
        accuracy: Current accuracy value (0-1)
        window_size: Size of the rolling window
        model_version: Version of the model
    """
    model_accuracy_rolling.labels(
        window_size=str(window_size),
        model_version=model_version
    ).set(accuracy)


def update_predictions_in_window(count: int, window_size: int = 100):
    """
    Update the count of predictions in the rolling window.
    
    Args:
        count: Number of predictions in window
        window_size: Size of the rolling window
    """
    model_predictions_in_window.labels(
        window_size=str(window_size)
    ).set(count)


# ========================== Metrics Endpoint ==========================

def metrics_endpoint():
    """
    FastAPI endpoint handler for Prometheus metrics.
    Returns metrics in Prometheus format.
    
    Usage in FastAPI:
        @app.get("/metrics")
        async def metrics():
            return metrics_endpoint()
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ========================== Drift Calculation Utilities ==========================

def calculate_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Calculate Population Stability Index (PSI) for drift detection.
    
    Args:
        expected: Training/baseline data distribution
        actual: Current/production data distribution
        bins: Number of bins for discretization
        
    Returns:
        PSI value (0 = no drift, >0.2 = significant drift)
    """
    try:
        # Create bins based on expected distribution
        breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
        breakpoints = np.unique(breakpoints)  # Remove duplicates
        
        # If we have too few unique breakpoints, use raw bins
        if len(breakpoints) < 3:
            breakpoints = np.linspace(expected.min(), expected.max(), bins + 1)
        
        # Calculate expected and actual distributions
        expected_percents = np.histogram(expected, bins=breakpoints)[0] / len(expected)
        actual_percents = np.histogram(actual, bins=breakpoints)[0] / len(actual)
        
        # Avoid division by zero
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
        
        # Calculate PSI
        psi = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
        
        return float(psi)
        
    except Exception as e:
        logging.error(f"Error calculating PSI: {str(e)}")
        return 0.0


def calculate_ks_statistic(expected: np.ndarray, actual: np.ndarray) -> float:
    """
    Calculate Kolmogorov-Smirnov statistic for drift detection.
    
    Args:
        expected: Training/baseline data distribution
        actual: Current/production data distribution
        
    Returns:
        KS statistic (0-1, higher = more drift)
    """
    try:
        ks_stat, _ = stats.ks_2samp(expected, actual)
        return float(ks_stat)
    except Exception as e:
        logging.error(f"Error calculating KS statistic: {str(e)}")
        return 0.0


def calculate_js_divergence(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Calculate Jensen-Shannon divergence for drift detection.
    
    Args:
        expected: Training/baseline data distribution
        actual: Current/production data distribution
        bins: Number of bins for discretization
        
    Returns:
        JS divergence (0 = identical, 1 = completely different)
    """
    try:
        # Create histograms
        min_val = min(expected.min(), actual.min())
        max_val = max(expected.max(), actual.max())
        bins_array = np.linspace(min_val, max_val, bins + 1)
        
        p = np.histogram(expected, bins=bins_array)[0] / len(expected)
        q = np.histogram(actual, bins=bins_array)[0] / len(actual)
        
        # Avoid log(0)
        p = np.where(p == 0, 1e-10, p)
        q = np.where(q == 0, 1e-10, q)
        
        # Calculate JS divergence
        m = 0.5 * (p + q)
        js = 0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m))
        
        return float(js)
        
    except Exception as e:
        logging.error(f"Error calculating JS divergence: {str(e)}")
        return 0.0


# ========================== Rolling Window Manager ==========================

class RollingAccuracyTracker:
    """
    Track rolling accuracy over a fixed window of predictions.
    """
    
    def __init__(self, window_size: int = 100, model_version: str = "v1.0"):
        """
        Initialize the tracker.
        
        Args:
            window_size: Number of predictions to keep in the window
            model_version: Version of the model being tracked
        """
        self.window_size = window_size
        self.model_version = model_version
        self.predictions = []
        self.actuals = []
        
    def add_prediction(self, prediction: int, actual: Optional[int] = None):
        """
        Add a new prediction-actual pair.
        
        Args:
            prediction: Predicted class
            actual: Actual class (if available)
        """
        if actual is not None:
            self.predictions.append(prediction)
            self.actuals.append(actual)
            
            # Keep only the last window_size predictions
            if len(self.predictions) > self.window_size:
                self.predictions.pop(0)
                self.actuals.pop(0)
            
            # Update metrics
            self._update_metrics()
    
    def _update_metrics(self):
        """Update Prometheus metrics with current accuracy."""
        if len(self.predictions) > 0:
            accuracy = np.mean(np.array(self.predictions) == np.array(self.actuals))
            update_rolling_accuracy(accuracy, self.window_size, self.model_version)
            update_predictions_in_window(len(self.predictions), self.window_size)
    
    def get_accuracy(self) -> Optional[float]:
        """Get current rolling accuracy."""
        if len(self.predictions) > 0:
            return float(np.mean(np.array(self.predictions) == np.array(self.actuals)))
        return None
