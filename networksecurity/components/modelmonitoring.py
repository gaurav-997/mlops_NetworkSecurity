"""
Model Monitoring Component for Drift Detection
Implements data drift, model drift, and concept drift detection.
"""
import os
import sys
import pickle
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
from networksecurity.utils.main_utils.prometheus_utils import (
    calculate_psi,
    calculate_ks_statistic,
    calculate_js_divergence,
    update_drift_score,
    RollingAccuracyTracker
)


@dataclass
class DriftConfig:
    """Configuration for drift detection."""
    psi_threshold: float = 0.2  # PSI > 0.2 indicates significant drift
    ks_threshold: float = 0.3   # KS statistic > 0.3 indicates drift
    js_threshold: float = 0.15  # JS divergence > 0.15 indicates drift
    accuracy_drop_threshold: float = 0.1  # 10% accuracy drop triggers alert
    window_size: int = 100  # Rolling window size for accuracy tracking
    baseline_stats_path: str = "baseline_stats"
    drift_reports_path: str = "drift_reports"
    check_interval: int = 50  # Check drift every N predictions


@dataclass
class BaselineStatistics:
    """Store baseline statistics for drift detection."""
    feature_means: Dict[str, float] = field(default_factory=dict)
    feature_stds: Dict[str, float] = field(default_factory=dict)
    feature_quantiles: Dict[str, Dict[str, float]] = field(default_factory=dict)
    feature_distributions: Dict[str, np.ndarray] = field(default_factory=dict)
    class_distribution: Dict[str, float] = field(default_factory=dict)
    total_samples: int = 0
    created_at: str = ""
    model_version: str = "v1.0"
    
    def save(self, filepath: str):
        """Save baseline statistics to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        logging.info(f"Baseline statistics saved to {filepath}")
    
    @staticmethod
    def load(filepath: str) -> 'BaselineStatistics':
        """Load baseline statistics from file."""
        with open(filepath, 'rb') as f:
            stats = pickle.load(f)
        logging.info(f"Baseline statistics loaded from {filepath}")
        return stats


@dataclass
class DriftReport:
    """Drift detection report."""
    timestamp: str
    data_drift_detected: bool
    model_drift_detected: bool
    concept_drift_detected: bool
    feature_drift_scores: Dict[str, float] = field(default_factory=dict)
    feature_drift_type: Dict[str, str] = field(default_factory=dict)
    class_distribution_shift: float = 0.0
    rolling_accuracy: Optional[float] = None
    accuracy_drop: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)
    
    def save(self, filepath: str):
        """Save drift report to JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        report_dict = {
            'timestamp': self.timestamp,
            'data_drift_detected': self.data_drift_detected,
            'model_drift_detected': self.model_drift_detected,
            'concept_drift_detected': self.concept_drift_detected,
            'feature_drift_scores': self.feature_drift_scores,
            'feature_drift_type': self.feature_drift_type,
            'class_distribution_shift': self.class_distribution_shift,
            'rolling_accuracy': self.rolling_accuracy,
            'accuracy_drop': self.accuracy_drop,
            'recommendations': self.recommendations
        }
        with open(filepath, 'w') as f:
            json.dump(report_dict, f, indent=2)
        logging.info(f"Drift report saved to {filepath}")


class ModelMonitor:
    """
    Monitor model for data drift, model drift, and concept drift.
    """
    
    def __init__(self, config: DriftConfig = None):
        """
        Initialize ModelMonitor.
        
        Args:
            config: DriftConfig object with thresholds and settings
        """
        self.config = config or DriftConfig()
        self.baseline_stats: Optional[BaselineStatistics] = None
        self.accuracy_tracker = RollingAccuracyTracker(
            window_size=self.config.window_size
        )
        self.prediction_buffer = []
        
        # Create directories
        os.makedirs(self.config.baseline_stats_path, exist_ok=True)
        os.makedirs(self.config.drift_reports_path, exist_ok=True)
    
    def create_baseline(
        self, 
        data: pd.DataFrame, 
        predictions: np.ndarray,
        model_version: str = "v1.0"
    ):
        """
        Create baseline statistics from training/validation data.
        
        Args:
            data: Training or validation DataFrame (features only)
            predictions: Model predictions on the data
            model_version: Version of the model
        """
        try:
            logging.info("Creating baseline statistics for drift detection")
            
            baseline = BaselineStatistics()
            baseline.model_version = model_version
            baseline.created_at = datetime.now().isoformat()
            baseline.total_samples = len(data)
            
            # Feature statistics
            for col in data.columns:
                baseline.feature_means[col] = float(data[col].mean())
                baseline.feature_stds[col] = float(data[col].std())
                baseline.feature_quantiles[col] = {
                    'q25': float(data[col].quantile(0.25)),
                    'q50': float(data[col].quantile(0.50)),
                    'q75': float(data[col].quantile(0.75))
                }
                baseline.feature_distributions[col] = data[col].values
            
            # Class distribution
            unique, counts = np.unique(predictions, return_counts=True)
            baseline.class_distribution = {
                str(int(cls)): float(count / len(predictions))
                for cls, count in zip(unique, counts)
            }
            
            self.baseline_stats = baseline
            
            # Save baseline
            baseline_file = os.path.join(
                self.config.baseline_stats_path,
                f"baseline_{model_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            )
            baseline.save(baseline_file)
            
            logging.info(f"Baseline created with {len(data)} samples")
            return baseline
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def load_baseline(self, filepath: str = None):
        """
        Load baseline statistics from file.
        
        Args:
            filepath: Path to baseline file. If None, loads the latest baseline.
        """
        try:
            if filepath is None:
                # Find latest baseline file
                baseline_files = [
                    f for f in os.listdir(self.config.baseline_stats_path)
                    if f.startswith('baseline_') and f.endswith('.pkl')
                ]
                if not baseline_files:
                    raise FileNotFoundError("No baseline statistics file found")
                baseline_files.sort(reverse=True)
                filepath = os.path.join(self.config.baseline_stats_path, baseline_files[0])
            
            self.baseline_stats = BaselineStatistics.load(filepath)
            logging.info(f"Loaded baseline from {filepath}")
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def detect_data_drift(
        self, 
        current_data: pd.DataFrame,
        drift_method: str = "psi"
    ) -> Tuple[bool, Dict[str, float], Dict[str, str]]:
        """
        Detect data drift by comparing current data with baseline.
        
        Args:
            current_data: Current production data (features only)
            drift_method: Method to use - "psi", "ks", or "js"
            
        Returns:
            Tuple of (drift_detected, drift_scores, drift_types)
        """
        try:
            if self.baseline_stats is None:
                raise ValueError("Baseline statistics not loaded. Call load_baseline() first.")
            
            logging.info(f"Detecting data drift using {drift_method} method")
            
            drift_scores = {}
            drift_types = {}
            drift_detected = False
            
            for col in current_data.columns:
                if col not in self.baseline_stats.feature_distributions:
                    logging.warning(f"Feature {col} not in baseline, skipping")
                    continue
                
                baseline_dist = self.baseline_stats.feature_distributions[col]
                current_dist = current_data[col].values
                
                # Calculate drift score
                if drift_method == "psi":
                    score = calculate_psi(baseline_dist, current_dist)
                    threshold = self.config.psi_threshold
                elif drift_method == "ks":
                    score = calculate_ks_statistic(baseline_dist, current_dist)
                    threshold = self.config.ks_threshold
                elif drift_method == "js":
                    score = calculate_js_divergence(baseline_dist, current_dist)
                    threshold = self.config.js_threshold
                else:
                    raise ValueError(f"Unknown drift method: {drift_method}")
                
                drift_scores[col] = score
                drift_types[col] = drift_method
                
                # Update Prometheus metrics
                update_drift_score(col, score, drift_method)
                
                # Check if drift exceeds threshold
                if score > threshold:
                    drift_detected = True
                    logging.warning(
                        f"Data drift detected in feature '{col}': "
                        f"{drift_method.upper()} = {score:.4f} (threshold: {threshold})"
                    )
            
            return drift_detected, drift_scores, drift_types
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def detect_model_drift(
        self, 
        predictions: np.ndarray
    ) -> Tuple[bool, float]:
        """
        Detect model drift by comparing prediction distribution with baseline.
        
        Args:
            predictions: Current predictions
            
        Returns:
            Tuple of (drift_detected, distribution_shift)
        """
        try:
            if self.baseline_stats is None:
                raise ValueError("Baseline statistics not loaded")
            
            logging.info("Detecting model drift (prediction distribution shift)")
            
            # Calculate current class distribution
            unique, counts = np.unique(predictions, return_counts=True)
            current_dist = {
                str(int(cls)): float(count / len(predictions))
                for cls, count in zip(unique, counts)
            }
            
            # Calculate distribution shift (KL divergence or simple difference)
            shift = 0.0
            for cls in self.baseline_stats.class_distribution.keys():
                baseline_prob = self.baseline_stats.class_distribution.get(cls, 0.0)
                current_prob = current_dist.get(cls, 0.0)
                shift += abs(current_prob - baseline_prob)
            
            # Model drift if distribution shifted significantly
            drift_detected = shift > 0.2  # 20% shift threshold
            
            if drift_detected:
                logging.warning(
                    f"Model drift detected: class distribution shift = {shift:.4f}"
                )
            
            # Update Prometheus metrics
            update_drift_score("class_distribution", shift, "distribution_shift")
            
            return drift_detected, shift
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def detect_concept_drift(
        self,
        prediction: int,
        actual: Optional[int] = None
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        """
        Detect concept drift when ground truth labels are available.
        
        Args:
            prediction: Model prediction
            actual: Actual ground truth label (if available)
            
        Returns:
            Tuple of (drift_detected, rolling_accuracy, accuracy_drop)
        """
        try:
            if actual is None:
                return False, None, None
            
            # Track prediction-actual pair
            self.accuracy_tracker.add_prediction(prediction, actual)
            
            current_accuracy = self.accuracy_tracker.get_accuracy()
            
            if current_accuracy is None:
                return False, None, None
            
            # Concept drift if accuracy dropped significantly
            # Compare with expected baseline accuracy (e.g., 0.85)
            expected_accuracy = 0.85  # This should come from model evaluation
            accuracy_drop = expected_accuracy - current_accuracy
            
            drift_detected = accuracy_drop > self.config.accuracy_drop_threshold
            
            if drift_detected:
                logging.warning(
                    f"Concept drift detected: accuracy dropped by {accuracy_drop:.2%}"
                )
            
            return drift_detected, current_accuracy, accuracy_drop
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def generate_drift_report(
        self,
        current_data: pd.DataFrame,
        predictions: np.ndarray,
        actuals: Optional[np.ndarray] = None
    ) -> DriftReport:
        """
        Generate comprehensive drift report.
        
        Args:
            current_data: Current production data
            predictions: Model predictions
            actuals: Ground truth labels (if available)
            
        Returns:
            DriftReport object
        """
        try:
            logging.info("Generating drift report")
            
            # Data drift
            data_drift, drift_scores, drift_types = self.detect_data_drift(current_data)
            
            # Model drift
            model_drift, dist_shift = self.detect_model_drift(predictions)
            
            # Concept drift
            concept_drift = False
            rolling_acc = None
            acc_drop = None
            
            if actuals is not None:
                for pred, actual in zip(predictions, actuals):
                    cd, acc, drop = self.detect_concept_drift(pred, actual)
                    if cd:
                        concept_drift = True
                rolling_acc = self.accuracy_tracker.get_accuracy()
                if rolling_acc is not None:
                    acc_drop = 0.85 - rolling_acc  # vs expected accuracy
            
            # Generate recommendations
            recommendations = []
            if data_drift:
                recommendations.append(
                    "Data drift detected. Consider retraining the model with recent data."
                )
            if model_drift:
                recommendations.append(
                    "Prediction distribution shifted. Investigate if this reflects real changes."
                )
            if concept_drift:
                recommendations.append(
                    f"Accuracy dropped by {acc_drop:.2%}. Retrain model immediately."
                )
            if not (data_drift or model_drift or concept_drift):
                recommendations.append("No significant drift detected. Model is stable.")
            
            # Create report
            report = DriftReport(
                timestamp=datetime.now().isoformat(),
                data_drift_detected=data_drift,
                model_drift_detected=model_drift,
                concept_drift_detected=concept_drift,
                feature_drift_scores=drift_scores,
                feature_drift_type=drift_types,
                class_distribution_shift=dist_shift,
                rolling_accuracy=rolling_acc,
                accuracy_drop=acc_drop,
                recommendations=recommendations
            )
            
            # Save report
            report_file = os.path.join(
                self.config.drift_reports_path,
                f"drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            report.save(report_file)
            
            return report
            
        except Exception as e:
            raise CustomException(e, sys)
