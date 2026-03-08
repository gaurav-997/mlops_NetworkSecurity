import os
import sys
import numpy as np

from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
from networksecurity.entity.config_entity import ModelEvaluationConfig
from networksecurity.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact,
    ClassificationMetricArtifact,
)
from networksecurity.utils.main_utils.utils import load_object, load_numpy_array_data, save_object

from sklearn.metrics import f1_score, precision_score, recall_score


class ModelEvaluation:
    def __init__(
        self,
        model_trainer_artifact: ModelTrainerArtifact,
        data_transformation_artifact: DataTransformationArtifact,
        model_evaluation_config: ModelEvaluationConfig,
    ):
        try:
            self.model_trainer_artifact = model_trainer_artifact
            self.data_transformation_artifact = data_transformation_artifact
            self.model_evaluation_config = model_evaluation_config
        except Exception as e:
            raise CustomException(e, sys)

    def get_classification_metric(self, y_true, y_pred) -> ClassificationMetricArtifact:
        try:
            return ClassificationMetricArtifact(
                f1_score=f1_score(y_true, y_pred),
                precision_score=precision_score(y_true, y_pred),
                recall_score=recall_score(y_true, y_pred),
            )
        except Exception as e:
            raise CustomException(e, sys)

    # Load previously saved production model from final_model/model.pkl (if it exists)
    def get_best_model(self):
        """Load the previously saved best model if it exists."""
        try:
            best_model_path = self.model_evaluation_config.best_model_file_path
            if not os.path.exists(best_model_path):
                logging.info("No existing best model found")
                return None
            model = load_object(file_path=best_model_path)
            logging.info(f"Loaded existing best model from {best_model_path}")
            return model
        except Exception as e:
            raise CustomException(e, sys)

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        try:
            logging.info("Model evaluation started")

            test_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_test_file_path
            )
            X_test, y_test = test_arr[:, :-1], test_arr[:, -1]

            trained_model = load_object(
                file_path=self.model_trainer_artifact.trained_model_file_path
            )
            y_pred_trained = trained_model.predict(X_test)
            trained_metric = self.get_classification_metric(y_test, y_pred_trained)
            logging.info(
                f"Trained model metrics - F1: {trained_metric.f1_score:.4f}, "
                f"Precision: {trained_metric.precision_score:.4f}, "
                f"Recall: {trained_metric.recall_score:.4f}"
            )

            best_model = self.get_best_model()

            # No production model exists yet — accept the trained model as the first best model
            if best_model is None:
                logging.info("No existing best model. Accepting the trained model.")
                is_model_accepted = True
                improved_accuracy = trained_metric.f1_score
                best_model_metric = trained_metric

                os.makedirs(self.model_evaluation_config.best_model_dir, exist_ok=True)
                save_object(
                    file_path=self.model_evaluation_config.best_model_file_path,
                    obj=trained_model,
                )
                logging.info(
                    f"Saved trained model as best model at "
                    f"{self.model_evaluation_config.best_model_file_path}"
                )
            # Compare new model vs existing best model — accept only if F1 improvement > change_threshold (0.02)
            else:
                y_pred_best = best_model.predict(X_test)
                best_model_metric = self.get_classification_metric(y_test, y_pred_best)
                logging.info(
                    f"Best model metrics - F1: {best_model_metric.f1_score:.4f}, "
                    f"Precision: {best_model_metric.precision_score:.4f}, "
                    f"Recall: {best_model_metric.recall_score:.4f}"
                )

                improved_accuracy = trained_metric.f1_score - best_model_metric.f1_score

                if improved_accuracy > self.model_evaluation_config.change_threshold:
                    is_model_accepted = True
                    save_object(
                        file_path=self.model_evaluation_config.best_model_file_path,
                        obj=trained_model,
                    )
                    logging.info(
                        f"Trained model accepted. Improvement: {improved_accuracy:.4f} "
                        f"(threshold: {self.model_evaluation_config.change_threshold})"
                    )
                else:
                    is_model_accepted = False
                    logging.info(
                        f"Trained model rejected. Improvement: {improved_accuracy:.4f} "
                        f"does not exceed threshold: {self.model_evaluation_config.change_threshold}"
                    )

            model_evaluation_artifact = ModelEvaluationArtifact(
                is_model_accepted=is_model_accepted,
                improved_accuracy=improved_accuracy,
                best_model_path=self.model_evaluation_config.best_model_file_path,
                trained_model_path=self.model_trainer_artifact.trained_model_file_path,
                train_metric_artifact=trained_metric,
                best_model_metric_artifact=best_model_metric,
            )

            logging.info(f"Model evaluation complete. Artifact: {model_evaluation_artifact}")
            return model_evaluation_artifact

        except Exception as e:
            raise CustomException(e, sys)
