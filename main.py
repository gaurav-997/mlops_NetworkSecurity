"""
Main entry point for the Network Security MLOps Training Pipeline.
This script initiates and runs the complete training pipeline orchestration.
"""
import sys
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
from networksecurity.pipeline.training_pipeline import TrainingPipeline


def main():
    """
    Main function to execute the training pipeline.
    """
    try:
        logging.info("Starting MLOps Network Security Training Pipeline")
        
        # Initialize and run the training pipeline
        training_pipeline = TrainingPipeline()
        training_pipeline.run_pipeline()
        
        logging.info("MLOps Network Security Training Pipeline completed successfully!")
        
    except Exception as e:
        logging.error(f"Training Pipeline execution failed: {str(e)}")
        raise CustomException(e, sys)


if __name__ == "__main__":
    main()
