"""
Scheduled Retraining Script
Run this script with cron (Linux) or Task Scheduler (Windows) for scheduled retraining.

Linux cron example (weekly on Sunday at 2 AM):
    0 2 * * 0 /usr/bin/python3 /path/to/scheduled_retrain.py

Windows Task Scheduler:
    - Open Task Scheduler
    - Create Basic Task
    - Set trigger (e.g., Weekly, Sunday, 2:00 AM)
    - Action: Start a program
    - Program: python
    - Arguments: C:\\path\\to\\scheduled_retrain.py
"""
import sys
import os
import argparse
from datetime import datetime

from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
from networksecurity.components.feedback_collector import FeedbackCollector
from networksecurity.pipeline.retraining_config import (
    RetrainingManager,
    RetrainingConfig,
    RetrainingTrigger,
    RetrainingStrategy
)


def send_notification(message: str, success: bool = True):
    """
    Send notification about retraining status.
    
    Args:
        message: Notification message
        success: Whether retraining was successful
    """
    try:
        # You can implement notification logic here:
        # - Send email
        # - Post to Slack
        # - Send SMS
        # - etc.
        
        status_emoji = "✅" if success else "❌"
        print(f"{status_emoji} {message}")
        logging.info(message)
        
        # Example: Send to Slack webhook (if configured)
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            import requests
            requests.post(slack_webhook, json={"text": f"{status_emoji} {message}"})
    
    except Exception as e:
        logging.error(f"Failed to send notification: {str(e)}")


def check_retraining_conditions(collector: FeedbackCollector, config: RetrainingConfig):
    """
    Check if retraining conditions are met.
    
    Returns:
        Tuple of (should_retrain, reason)
    """
    try:
        # Get feedback statistics
        stats = collector.get_statistics()
        logging.info(f"Feedback statistics: {stats}")
        
        # Check data-based trigger
        should_retrain, reason = collector.should_trigger_retraining(
            min_new_samples=config.min_new_samples,
            accuracy_threshold=0.75
        )
        
        if should_retrain:
            return True, reason
        
        # Check if enough labeled data exists
        if stats['labeled_records'] >= config.min_new_samples:
            return True, f"Scheduled retraining - {stats['labeled_records']} labeled samples available"
        
        return False, f"Insufficient data: {stats['labeled_records']} labeled samples (minimum: {config.min_new_samples})"
    
    except Exception as e:
        raise CustomException(e, sys)


def main():
    """Main entry point for scheduled retraining."""
    parser = argparse.ArgumentParser(description='Scheduled model retraining script')
    parser.add_argument(
        '--strategy',
        type=str,
        default='incremental',
        choices=['full', 'incremental', 'windowed'],
        help='Retraining data strategy'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force retraining even if conditions are not met'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check conditions without retraining'
    )
    
    args = parser.parse_args()
    
    try:
        logging.info("=" * 70)
        logging.info("SCHEDULED RETRAINING SCRIPT STARTED")
        logging.info(f"Time: {datetime.now().isoformat()}")
        logging.info(f"Strategy: {args.strategy}")
        logging.info("=" * 70)
        
        # Initialize components
        collector = FeedbackCollector()
        
        config = RetrainingConfig(
            retraining_strategy=RetrainingStrategy(args.strategy)
        )
        config.validate()
        
        manager = RetrainingManager(config)
        
        # Check conditions
        should_retrain, reason = check_retraining_conditions(collector, config)
        
        logging.info(f"Retraining check: should_retrain={should_retrain}, reason={reason}")
        
        if args.check_only:
            print(f"Check only mode:")
            print(f"  Should retrain: {should_retrain}")
            print(f"  Reason: {reason}")
            return
        
        # Override if force flag is set
        if args.force:
            should_retrain = True
            reason = "Forced retraining via --force flag"
            logging.info(reason)
        
        if not should_retrain:
            message = f"Retraining skipped: {reason}"
            logging.info(message)
            send_notification(message, success=True)
            return
        
        # Check frequency limit
        last_retrain = manager.get_last_retrain_time()
        if not config.should_retrain_now(last_retrain):
            message = (
                f"Retraining skipped: Last retrain was too recent "
                f"(within {config.max_retrain_frequency_hours} hours)"
            )
            logging.warning(message)
            send_notification(message, success=True)
            return
        
        # Trigger retraining
        logging.info(f"Starting retraining: {reason}")
        send_notification(f"🚀 Retraining started: {reason}")
        
        success = manager.trigger_retraining(
            trigger_type=RetrainingTrigger.SCHEDULED,
            reason=reason
        )
        
        if success:
            message = f"✅ Retraining completed successfully: {reason}"
            logging.info(message)
            send_notification(message, success=True)
            
            # Export updated statistics
            stats = collector.get_statistics()
            logging.info(f"Post-retraining statistics: {stats}")
        else:
            message = "❌ Retraining failed"
            logging.error(message)
            send_notification(message, success=False)
            sys.exit(1)
        
    except Exception as e:
        error_msg = f"❌ Retraining script failed: {str(e)}"
        logging.error(error_msg)
        send_notification(error_msg, success=False)
        raise CustomException(e, sys)
    
    finally:
        logging.info("=" * 70)
        logging.info("SCHEDULED RETRAINING SCRIPT COMPLETED")
        logging.info("=" * 70)


if __name__ == "__main__":
    main()
