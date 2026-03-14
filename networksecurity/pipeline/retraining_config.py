"""
Retraining Configuration and Strategy
Manages retraining triggers, data strategy, and execution.
"""
import os
import sys
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException


class RetrainingStrategy(Enum):
    """Retraining data strategy options."""
    FULL = "full"  # Use all historical data
    INCREMENTAL = "incremental"  # Append new data to existing
    WINDOWED = "windowed"  # Use only recent N days/months


class RetrainingTrigger(Enum):
    """Types of retraining triggers."""
    SCHEDULED = "scheduled"  # Cron/scheduled job
    DRIFT_BASED = "drift_based"  # Triggered by drift alert
    DATA_BASED = "data_based"  # Triggered by new labeled data threshold
    MANUAL = "manual"  # Manual trigger


@dataclass
class RetrainingConfig:
    """Configuration for model retraining."""
    
    # Trigger settings
    min_new_samples: int = 1000  # Min new labeled samples to trigger retraining
    drift_threshold_psi: float = 0.2  # PSI threshold for drift-based retraining
    accuracy_drop_threshold: float = 0.10  # 10% accuracy drop triggers retraining
    
    # Scheduling (for scheduled retraining)
    schedule_cron: str = "0 2 * * 0"  # Weekly at 2 AM Sunday (cron format)
    schedule_enabled: bool = False
    
    # Data strategy
    retraining_strategy: RetrainingStrategy = RetrainingStrategy.INCREMENTAL
    window_days: int = 90  # For windowed strategy: use last 90 days
    
    # Data sources
    feedback_db_path: str = "feedback_data/feedback.db"
    original_data_path: str = "Network_data/phisingData.csv"
    retraining_data_path: str = "feedback_data/retraining_data.csv"
    
    # Version control
    use_dvc: bool = True  # Version data with DVC before retraining
    use_mlflow: bool = True  # Log data version in MLflow
    
    # Model versioning
    model_version_format: str = "v{major}.{minor}.{patch}"  # Semantic versioning
    auto_increment_version: bool = True
    
    # Deployment strategy
    auto_deploy_after_training: bool = False  # Auto-deploy if model accepted
    require_manual_approval: bool = True  # Require manual approval before deploy
    
    # Notification settings
    notify_on_trigger: bool = True
    notification_webhook: Optional[str] = None  # Slack/Teams webhook URL
    
    # Safety checks
    min_train_samples: int = 1000  # Minimum samples required for retraining
    max_retrain_frequency_hours: int = 24  # Don't retrain more than once per day
    
    def validate(self) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            True if valid, raises exception otherwise
        """
        try:
            if self.min_new_samples < 100:
                raise ValueError("min_new_samples must be at least 100")
            
            if not (0 < self.drift_threshold_psi < 1):
                raise ValueError("drift_threshold_psi must be between 0 and 1")
            
            if not (0 < self.accuracy_drop_threshold < 1):
                raise ValueError("accuracy_drop_threshold must be between 0 and 1")
            
            if self.retraining_strategy == RetrainingStrategy.WINDOWED and self.window_days < 7:
                raise ValueError("window_days must be at least 7 for windowed strategy")
            
            if not os.path.exists(self.original_data_path):
                logging.warning(f"Original data path does not exist: {self.original_data_path}")
            
            return True
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def should_retrain_now(self, last_retrain_time: Optional[datetime] = None) -> bool:
        """
        Check if retraining should proceed based on frequency limits.
        
        Args:
            last_retrain_time: Timestamp of last retraining
            
        Returns:
            True if retraining is allowed
        """
        if last_retrain_time is None:
            return True
        
        time_since_last = datetime.now() - last_retrain_time
        min_interval = timedelta(hours=self.max_retrain_frequency_hours)
        
        if time_since_last < min_interval:
            logging.warning(
                f"Retraining skipped: last retrain was {time_since_last} ago "
                f"(minimum interval: {min_interval})"
            )
            return False
        
        return True


class RetrainingManager:
    """
    Manages retraining triggers, data preparation, and execution.
    """
    
    def __init__(self, config: Optional[RetrainingConfig] = None):
        """
        Initialize RetrainingManager.
        
        Args:
            config: RetrainingConfig object
        """
        self.config = config or RetrainingConfig()
        self.config.validate()
        self.last_retrain_file = "retraining_metadata/last_retrain.txt"
    
    def get_last_retrain_time(self) -> Optional[datetime]:
        """Get timestamp of last retraining."""
        try:
            if os.path.exists(self.last_retrain_file):
                with open(self.last_retrain_file, 'r') as f:
                    timestamp_str = f.read().strip()
                    return datetime.fromisoformat(timestamp_str)
            return None
        except Exception as e:
            logging.error(f"Error reading last retrain time: {str(e)}")
            return None
    
    def update_last_retrain_time(self):
        """Update last retraining timestamp."""
        try:
            os.makedirs(os.path.dirname(self.last_retrain_file), exist_ok=True)
            with open(self.last_retrain_file, 'w') as f:
                f.write(datetime.now().isoformat())
            logging.info("Updated last retrain timestamp")
        except Exception as e:
            logging.error(f"Error updating last retrain time: {str(e)}")
    
    def prepare_retraining_data(self) -> Optional[str]:
        """
        Prepare data for retraining based on strategy.
        
        Returns:
            Path to prepared data file, or None if preparation failed
        """
        try:
            logging.info(f"Preparing data with {self.config.retraining_strategy.value} strategy")
            
            if self.config.retraining_strategy == RetrainingStrategy.FULL:
                return self._prepare_full_retrain_data()
            
            elif self.config.retraining_strategy == RetrainingStrategy.INCREMENTAL:
                return self._prepare_incremental_data()
            
            elif self.config.retraining_strategy == RetrainingStrategy.WINDOWED:
                return self._prepare_windowed_data()
            
            else:
                raise ValueError(f"Unknown strategy: {self.config.retraining_strategy}")
                
        except Exception as e:
            raise CustomException(e, sys)
    
    def _prepare_full_retrain_data(self) -> Optional[str]:
        """Prepare data for full retrain (all historical + new)."""
        try:
            import pandas as pd
            from networksecurity.components.feedback_collector import FeedbackCollector
            
            # Load original training data
            original_data = pd.read_csv(self.config.original_data_path)
            logging.info(f"Loaded {len(original_data)} samples from original data")
            
            # Load feedback data
            collector = FeedbackCollector(self.config.feedback_db_path)
            feedback_df = collector.get_labeled_data()
            
            if not feedback_df.empty:
                # Extract features
                features_df = pd.DataFrame(feedback_df['features'].tolist())
                features_df['Result'] = feedback_df['actual_label'].values
                
                # Combine datasets
                combined_data = pd.concat([original_data, features_df], ignore_index=True)
                logging.info(f"Combined data: {len(combined_data)} total samples")
            else:
                combined_data = original_data
                logging.warning("No feedback data available, using original data only")
            
            # Save combined data
            output_path = self.config.retraining_data_path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            combined_data.to_csv(output_path, index=False)
            
            logging.info(f"Prepared full retrain data: {output_path}")
            return output_path
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def _prepare_incremental_data(self) -> Optional[str]:
        """Prepare incremental data (append new feedback to original)."""
        return self._prepare_full_retrain_data()  # Same as full for this implementation
    
    def _prepare_windowed_data(self) -> Optional[str]:
        """Prepare windowed data (only recent N days)."""
        try:
            import pandas as pd
            from networksecurity.components.feedback_collector import FeedbackCollector
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=self.config.window_days)).isoformat()
            
            # Load feedback data within window
            collector = FeedbackCollector(self.config.feedback_db_path)
            feedback_df = collector.get_labeled_data(start_date=cutoff_date)
            
            if len(feedback_df) < self.config.min_train_samples:
                logging.warning(
                    f"Insufficient data in {self.config.window_days}-day window: "
                    f"{len(feedback_df)} samples (minimum: {self.config.min_train_samples})"
                )
                # Fall back to full data
                return self._prepare_full_retrain_data()
            
            # Extract features
            features_df = pd.DataFrame(feedback_df['features'].tolist())
            features_df['Result'] = feedback_df['actual_label'].values
            
            # Save windowed data
            output_path = self.config.retraining_data_path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            features_df.to_csv(output_path, index=False)
            
            logging.info(
                f"Prepared windowed data ({self.config.window_days} days): "
                f"{len(features_df)} samples at {output_path}"
            )
            return output_path
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def trigger_retraining(
        self,
        trigger_type: RetrainingTrigger,
        reason: str = ""
    ) -> bool:
        """
        Trigger the retraining pipeline.
        
        Args:
            trigger_type: Type of trigger
            reason: Reason for retraining
            
        Returns:
            True if retraining was triggered successfully
        """
        try:
            logging.info(f"Retraining trigger: {trigger_type.value} - {reason}")
            
            # Check frequency limit
            last_retrain = self.get_last_retrain_time()
            if not self.config.should_retrain_now(last_retrain):
                return False
            
            # Prepare data
            data_path = self.prepare_retraining_data()
            if data_path is None:
                logging.error("Failed to prepare retraining data")
                return False
            
            # Version data with DVC if enabled
            if self.config.use_dvc:
                self._version_data_with_dvc(data_path)
            
            # Trigger training pipeline
            from networksecurity.pipeline.training_pipeline import TrainingPipeline
            
            pipeline = TrainingPipeline()
            pipeline.run_pipeline()
            
            # Update last retrain time
            self.update_last_retrain_time()
            
            logging.info("Retraining completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Retraining failed: {str(e)}")
            raise CustomException(e, sys)
    
    def _version_data_with_dvc(self, data_path: str):
        """Version data with DVC before retraining."""
        try:
            import subprocess
            
            # Add file to DVC
            result = subprocess.run(
                ['dvc', 'add', data_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logging.info(f"Data versioned with DVC: {data_path}")
                
                # Commit DVC file
                subprocess.run(['git', 'add', f'{data_path}.dvc'])
                subprocess.run([
                    'git', 'commit', '-m', 
                    f'Version retraining data from {datetime.now().strftime("%Y-%m-%d")}'
                ])
            else:
                logging.warning(f"DVC versioning failed: {result.stderr}")
                
        except FileNotFoundError:
            logging.warning("DVC not installed, skipping data versioning")
        except Exception as e:
            logging.error(f"Error versioning data with DVC: {str(e)}")
