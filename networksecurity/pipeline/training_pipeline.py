import os
import sys
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException

# Import all config entities
from networksecurity.entity.config_entity import (
    TrainingPipelineConfig,
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelEvaluationConfig,
    ModelPusherConfig,
)

# Import all artifact entities
from networksecurity.entity.artifact_entity import (
    DataIngestionArtifact,
    DataValidationArtifact,
    DataTransformationArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact,
    ModelPusherArtifact,
)

# Import all components
from networksecurity.components.dataingestion import DataIngestion
from networksecurity.components.datavalidation import DataValidation
from networksecurity.components.datatransformation import DataTransformation
from networksecurity.components.modeltraining import ModelTraining
from networksecurity.components.modelevaluation import ModelEvaluation
from networksecurity.components.modelpusher import ModelPusher


class TrainingPipeline:
    def __init__(self):
        """
        Initialize the training pipeline with default configuration.
        """
        self.training_pipeline_config = TrainingPipelineConfig()

    def start_data_ingestion(self) -> DataIngestionArtifact:
        """
        Start the data ingestion process.
        Returns:
            DataIngestionArtifact: Artifact containing paths to train and test data
        """
        try:
            logging.info("=" * 70)
            logging.info("Starting Data Ingestion")
            logging.info("=" * 70)

            data_ingestion_config = DataIngestionConfig(trainingpipelineconfig=self.training_pipeline_config)
            data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()

            logging.info(f"Data Ingestion completed: {data_ingestion_artifact}")
            logging.info("=" * 70)

            return data_ingestion_artifact

        except Exception as e:
            logging.error(f"Data Ingestion failed: {str(e)}")
            raise CustomException(e, sys)

    def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
        """
        Start the data validation process.
        Args:
            data_ingestion_artifact: Output from data ingestion stage
        Returns:
            DataValidationArtifact: Artifact containing validation status and drift report
        """
        try:
            logging.info("=" * 70)
            logging.info("Starting Data Validation")
            logging.info("=" * 70)

            data_validation_config = DataValidationConfig(trainingpipelineconfig=self.training_pipeline_config)
            data_validation = DataValidation(data_ingestion_artifact=data_ingestion_artifact,data_validation_config=data_validation_config)
            data_validation_artifact = data_validation.initiate_data_validation()

            logging.info(f"Data Validation completed: {data_validation_artifact}")
            logging.info("=" * 70)

            return data_validation_artifact

        except Exception as e:
            logging.error(f"Data Validation failed: {str(e)}")
            raise CustomException(e, sys)

    def start_data_transformation(self, data_validation_artifact: DataValidationArtifact) -> DataTransformationArtifact:
        """
        Start the data transformation process.
        Args:
            data_validation_artifact: Output from data validation stage
        Returns:
            DataTransformationArtifact: Artifact containing transformed data paths and preprocessing object
        """
        try:
            logging.info("=" * 70)
            logging.info("Starting Data Transformation")
            logging.info("=" * 70)

            data_transformation_config = DataTransformationConfig(trainingpipelineconfig=self.training_pipeline_config)
            data_transformation = DataTransformation(data_validation_artifact=data_validation_artifact,data_transformation_config=data_transformation_config)
            data_transformation_artifact = data_transformation.initiate_data_transformation()

            logging.info(f"Data Transformation completed: {data_transformation_artifact}")
            logging.info("=" * 70)

            return data_transformation_artifact

        except Exception as e:
            logging.error(f"Data Transformation failed: {str(e)}")
            raise CustomException(e, sys)

    def start_model_training(self, data_transformation_artifact: DataTransformationArtifact) -> ModelTrainerArtifact:
        """
        Start the model training process.
        Args:
            data_transformation_artifact: Output from data transformation stage
        Returns:
            ModelTrainerArtifact: Artifact containing trained model path and metrics
        """
        try:
            logging.info("=" * 70)
            logging.info("Starting Model Training")
            logging.info("=" * 70)

            model_trainer_config = ModelTrainerConfig(trainingpipelineconfig=self.training_pipeline_config)
            model_trainer = ModelTraining(data_transformation_artifact=data_transformation_artifact,model_trainer_config=model_trainer_config)
            model_trainer_artifact = model_trainer.initiate_model_training()

            logging.info(f"Model Training completed: {model_trainer_artifact}")
            logging.info("=" * 70)

            return model_trainer_artifact

        except Exception as e:
            logging.error(f"Model Training failed: {str(e)}")
            raise CustomException(e, sys)

    def start_model_evaluation(
        self,
        model_trainer_artifact: ModelTrainerArtifact,
        data_transformation_artifact: DataTransformationArtifact,
    ) -> ModelEvaluationArtifact:
        """
        Start the model evaluation process.
        Args:
            model_trainer_artifact: Output from model training stage
            data_transformation_artifact: Output from data transformation stage
        Returns:
            ModelEvaluationArtifact: Artifact containing model acceptance status and metrics
        """
        try:
            logging.info("=" * 70)
            logging.info("Starting Model Evaluation")
            logging.info("=" * 70)

            model_evaluation_config = ModelEvaluationConfig(trainingpipelineconfig=self.training_pipeline_config)
            model_evaluation = ModelEvaluation(
                model_trainer_artifact=model_trainer_artifact,
                data_transformation_artifact=data_transformation_artifact,
                model_evaluation_config=model_evaluation_config,
            )
            model_evaluation_artifact = model_evaluation.initiate_model_evaluation()

            logging.info(f"Model Evaluation completed: {model_evaluation_artifact}")
            logging.info("=" * 70)

            return model_evaluation_artifact

        except Exception as e:
            logging.error(f"Model Evaluation failed: {str(e)}")
            raise CustomException(e, sys)

    def start_model_pusher(
        self, model_evaluation_artifact: ModelEvaluationArtifact
    ) -> ModelPusherArtifact:
        """
        Start the model pusher process (only if model is accepted).
        Args:
            model_evaluation_artifact: Output from model evaluation stage
        Returns:
            ModelPusherArtifact: Artifact containing model deployment paths
        """
        try:
            logging.info("=" * 70)
            logging.info("Starting Model Pusher")
            logging.info("=" * 70)

            # Check if model is accepted before pushing
            if not model_evaluation_artifact.is_model_accepted:
                logging.warning(
                    "Model is not accepted. Skipping Model Pusher stage."
                )
                raise Exception(
                    "Model is not accepted by evaluation stage. "
                    "Model Pusher will not proceed."
                )

            model_pusher_config = ModelPusherConfig(
                trainingpipelineconfig=self.training_pipeline_config
            )
            model_pusher = ModelPusher(
                model_evaluation_artifact=model_evaluation_artifact,
                model_pusher_config=model_pusher_config,
            )
            model_pusher_artifact = model_pusher.initiate_model_pusher()

            logging.info(f"Model Pusher completed: {model_pusher_artifact}")
            logging.info("=" * 70)

            return model_pusher_artifact

        except Exception as e:
            logging.error(f"Model Pusher failed: {str(e)}")
            raise CustomException(e, sys)

    def run_pipeline(self):
        """
        Orchestrates the entire training pipeline in sequence.
        Stops the pipeline on failure at any stage.
        """
        try:
            logging.info("\n\n")
            logging.info("*" * 70)
            logging.info("TRAINING PIPELINE STARTED")
            logging.info("*" * 70)

            # Stage 1: Data Ingestion
            data_ingestion_artifact = self.start_data_ingestion()

            # Stage 2: Data Validation
            data_validation_artifact = self.start_data_validation(
                data_ingestion_artifact=data_ingestion_artifact
            )

            # Stage 3: Data Transformation
            data_transformation_artifact = self.start_data_transformation(
                data_validation_artifact=data_validation_artifact
            )

            # Stage 4: Model Training
            model_trainer_artifact = self.start_model_training(data_transformation_artifact=data_transformation_artifact)

            # Stage 5: Model Evaluation
            model_evaluation_artifact = self.start_model_evaluation(
                model_trainer_artifact=model_trainer_artifact,
                data_transformation_artifact=data_transformation_artifact,
            )

            # Stage 6: Model Pusher (only if model is accepted)
            if model_evaluation_artifact.is_model_accepted:
                model_pusher_artifact = self.start_model_pusher(
                    model_evaluation_artifact=model_evaluation_artifact
                )
                logging.info(
                    f"Model successfully pushed to production: {model_pusher_artifact}"
                )
            else:
                logging.warning(
                    "Model is not accepted. Skipping Model Pusher stage. "
                    "Pipeline completed without model deployment."
                )

            logging.info("*" * 70)
            logging.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
            logging.info("*" * 70)

        except Exception as e:
            logging.error("*" * 70)
            logging.error("TRAINING PIPELINE FAILED")
            logging.error(f"Error: {str(e)}")
            logging.error("*" * 70)
            raise CustomException(e, sys)
