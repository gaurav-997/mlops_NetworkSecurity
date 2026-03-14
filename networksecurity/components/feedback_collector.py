"""
Feedback Collection Component
Stores ground truth labels and user feedback for concept drift detection and model retraining.
"""
import os
import sys
import json
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException


@dataclass
class FeedbackRecord:
    """Single feedback record schema."""
    request_id: str
    timestamp: str
    prediction: int
    actual_label: Optional[int] = None
    user_feedback: Optional[str] = None  # 'correct' or 'incorrect'
    features: Optional[Dict[str, float]] = None
    model_version: str = "v1.0"
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class FeedbackCollector:
    """
    Collects and stores feedback and ground truth labels for model retraining.
    """
    
    def __init__(self, db_path: str = "feedback_data/feedback.db"):
        """
        Initialize FeedbackCollector with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with feedback table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    request_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    prediction INTEGER NOT NULL,
                    actual_label INTEGER,
                    user_feedback TEXT,
                    features TEXT,
                    model_version TEXT,
                    confidence REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index on timestamp for efficient queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON feedback(timestamp)
            ''')
            
            # Create index on model_version
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_model_version 
                ON feedback(model_version)
            ''')
            
            conn.commit()
            conn.close()
            
            logging.info(f"Feedback database initialized at {self.db_path}")
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def store_prediction(
        self,
        request_id: str,
        prediction: int,
        features: Dict[str, float],
        model_version: str = "v1.0",
        confidence: Optional[float] = None
    ):
        """
        Store a prediction for later feedback collection.
        
        Args:
            request_id: Unique identifier for the request
            prediction: Model prediction (0 or 1)
            features: Input features dictionary
            model_version: Version of model used
            confidence: Prediction confidence score
        """
        try:
            record = FeedbackRecord(
                request_id=request_id,
                timestamp=datetime.now().isoformat(),
                prediction=prediction,
                features=features,
                model_version=model_version,
                confidence=confidence
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO feedback 
                (request_id, timestamp, prediction, features, model_version, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                record.request_id,
                record.timestamp,
                record.prediction,
                json.dumps(record.features),
                record.model_version,
                record.confidence
            ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Stored prediction for request_id: {request_id}")
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def update_ground_truth(
        self,
        request_id: str,
        actual_label: int,
        user_feedback: Optional[str] = None
    ):
        """
        Update a prediction record with ground truth label.
        
        Args:
            request_id: Request ID to update
            actual_label: Ground truth label (0 or 1)
            user_feedback: Optional user feedback ('correct' or 'incorrect')
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE feedback 
                SET actual_label = ?, user_feedback = ?
                WHERE request_id = ?
            ''', (actual_label, user_feedback, request_id))
            
            if cursor.rowcount == 0:
                logging.warning(f"No record found for request_id: {request_id}")
            else:
                logging.info(f"Updated ground truth for request_id: {request_id}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def get_labeled_data(
        self,
        min_samples: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve labeled data for retraining.
        
        Args:
            min_samples: Minimum number of samples to retrieve
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            model_version: Filter by model version
            
        Returns:
            DataFrame with labeled data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT request_id, timestamp, prediction, actual_label, 
                       features, model_version, confidence
                FROM feedback 
                WHERE actual_label IS NOT NULL
            '''
            
            params = []
            
            if start_date:
                query += ' AND timestamp >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND timestamp <= ?'
                params.append(end_date)
            
            if model_version:
                query += ' AND model_version = ?'
                params.append(model_version)
            
            query += ' ORDER BY timestamp DESC'
            
            if min_samples:
                query += f' LIMIT {min_samples}'
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Parse features JSON
            if not df.empty and 'features' in df.columns:
                df['features'] = df['features'].apply(json.loads)
            
            logging.info(f"Retrieved {len(df)} labeled samples from feedback database")
            return df
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the feedback database.
        
        Returns:
            Dictionary with statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total records
            cursor.execute('SELECT COUNT(*) FROM feedback')
            total_records = cursor.fetchone()[0]
            
            # Labeled records
            cursor.execute('SELECT COUNT(*) FROM feedback WHERE actual_label IS NOT NULL')
            labeled_records = cursor.fetchone()[0]
            
            # Records by model version
            cursor.execute('''
                SELECT model_version, COUNT(*) 
                FROM feedback 
                GROUP BY model_version
            ''')
            by_version = dict(cursor.fetchall())
            
            # Accuracy (when labels available)
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN prediction = actual_label THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as accuracy
                FROM feedback 
                WHERE actual_label IS NOT NULL
            ''')
            accuracy_result = cursor.fetchone()[0]
            accuracy = float(accuracy_result) if accuracy_result else None
            
            conn.close()
            
            stats = {
                'total_records': total_records,
                'labeled_records': labeled_records,
                'unlabeled_records': total_records - labeled_records,
                'labeling_rate': labeled_records / total_records if total_records > 0 else 0,
                'records_by_version': by_version,
                'accuracy': accuracy
            }
            
            logging.info(f"Feedback statistics: {stats}")
            return stats
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def export_for_retraining(
        self,
        output_path: str = "feedback_data/retraining_data.csv",
        min_samples: int = 100
    ) -> Optional[str]:
        """
        Export labeled data for retraining in CSV format.
        
        Args:
            output_path: Path to save CSV file
            min_samples: Minimum samples required for export
            
        Returns:
            Path to exported file, or None if insufficient data
        """
        try:
            df = self.get_labeled_data()
            
            if len(df) < min_samples:
                logging.warning(
                    f"Insufficient labeled data for retraining: "
                    f"{len(df)} samples (minimum: {min_samples})"
                )
                return None
            
            # Extract features into columns
            if not df.empty:
                features_df = pd.DataFrame(df['features'].tolist())
                features_df['Result'] = df['actual_label'].values
                
                # Save to CSV
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                features_df.to_csv(output_path, index=False)
                
                logging.info(
                    f"Exported {len(features_df)} labeled samples to {output_path}"
                )
                return output_path
            
            return None
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def should_trigger_retraining(
        self,
        min_new_samples: int = 1000,
        accuracy_threshold: float = 0.75
    ) -> tuple[bool, str]:
        """
        Check if retraining should be triggered based on feedback data.
        
        Args:
            min_new_samples: Minimum new labeled samples to trigger retraining
            accuracy_threshold: Minimum accuracy to avoid triggering
            
        Returns:
            Tuple of (should_retrain, reason)
        """
        try:
            stats = self.get_statistics()
            
            # Check if we have enough new labeled samples
            if stats['labeled_records'] >= min_new_samples:
                return True, f"Sufficient labeled data: {stats['labeled_records']} samples"
            
            # Check if accuracy dropped
            if stats['accuracy'] is not None and stats['accuracy'] < accuracy_threshold:
                return True, f"Accuracy dropped to {stats['accuracy']:.2%} (threshold: {accuracy_threshold:.2%})"
            
            return False, "No retraining trigger conditions met"
            
        except Exception as e:
            raise CustomException(e, sys)
