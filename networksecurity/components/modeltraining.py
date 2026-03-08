import os 
import sys
import numpy as np

from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException
from networksecurity.entity.config_entity import ModelTrainerConfig
from networksecurity.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
    ClassificationMetricArtifact,
)
from networksecurity.utils.main_utils.utils import save_object, load_numpy_array_data

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (RandomForestClassifier,AdaBoostClassifier,GradientBoostingClassifier)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score, precision_score, recall_score


class ModelTraining:
    def __init__(
        self,
        data_transformation_artifact: DataTransformationArtifact,
        model_trainer_config: ModelTrainerConfig,
    ):
        try:
            self.data_transformation_artifact = data_transformation_artifact
            self.model_trainer_config = model_trainer_config
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

    # Model Selection: trains all 6 candidate algorithms ( logistic regression ,RandomForestClassifier,AdaBoostClassifier,
    # GradientBoostingClassifier,KNeighborsClassifier,DecisionTreeClassifier) and picks the best based on test F1 score
    def select_best_model(self, X_train, y_train, X_test, y_test):
        """Train all candidate models and return the best one based on test F1 score."""
        try:
            models = {
                "Random Forest": RandomForestClassifier(verbose=0),
                "Decision Tree": DecisionTreeClassifier(),
                "Gradient Boosting": GradientBoostingClassifier(verbose=0),
                "Logistic Regression": LogisticRegression(max_iter=1000),
                "AdaBoost": AdaBoostClassifier(),
                "KNN": KNeighborsClassifier(),
            }

            report = {}
            for model_name, model in models.items():
                model.fit(X_train, y_train)

                y_test_pred = model.predict(X_test)
                test_f1 = f1_score(y_test, y_test_pred)
                report[model_name] = {"model": model, "test_f1": test_f1}
                logging.info(f"{model_name} - Test F1: {test_f1:.4f}")

            best_model_name = max(report, key=lambda k: report[k]["test_f1"])
            best_entry = report[best_model_name]

            logging.info(
                f"Best model: {best_model_name} with Test F1: {best_entry['test_f1']:.4f}"
            )
            return best_entry["model"], best_model_name, best_entry["test_f1"]

        except Exception as e:
            raise CustomException(e, sys)

    def initiate_model_training(self) -> ModelTrainerArtifact:
        try:
            logging.info("Loading transformed train and test numpy arrays")
            train_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_train_file_path
            )
            test_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_test_file_path
            )

            X_train, y_train = train_arr[:, :-1], train_arr[:, -1]
            X_test, y_test = test_arr[:, :-1], test_arr[:, -1]

            logging.info("Evaluating multiple models to find the best one")
            best_model, best_model_name, best_test_f1 = self.select_best_model(
                X_train, y_train, X_test, y_test
            )

            # Reject if the best model's test F1 doesn't meet the minimum threshold (0.6)
            if best_test_f1 < self.model_trainer_config.expected_accuracy:
                raise Exception(
                    f"No model meets the expected accuracy threshold "
                    f"({self.model_trainer_config.expected_accuracy}). "
                    f"Best test F1: {best_test_f1:.4f}"
                )

            y_train_pred = best_model.predict(X_train)
            train_metric = self.get_classification_metric(y_train, y_train_pred)

            y_test_pred = best_model.predict(X_test)
            test_metric = self.get_classification_metric(y_test, y_test_pred)

            # Overfitting/Underfitting check: reject if train-test F1 gap exceeds threshold (0.05)
            diff = abs(train_metric.f1_score - test_metric.f1_score)
            if diff > self.model_trainer_config.overfitting_underfitting_threshold:
                raise Exception(
                    f"Model is overfitting/underfitting. "
                    f"Train F1: {train_metric.f1_score:.4f}, "
                    f"Test F1: {test_metric.f1_score:.4f}, "
                    f"Diff: {diff:.4f} > threshold "
                    f"{self.model_trainer_config.overfitting_underfitting_threshold}"
                )

            logging.info(f"Saving best model ({best_model_name}) to {self.model_trainer_config.trained_model_file_path}")
            save_object(
                file_path=self.model_trainer_config.trained_model_file_path,
                obj=best_model,
            )

            model_trainer_artifact = ModelTrainerArtifact(
                trained_model_file_path=self.model_trainer_config.trained_model_file_path,
                train_metric_artifact=train_metric,
                test_metric_artifact=test_metric,
            )

            logging.info(f"Model training complete. Artifact: {model_trainer_artifact}")
            return model_trainer_artifact

        except Exception as e:
            raise CustomException(e, sys)
