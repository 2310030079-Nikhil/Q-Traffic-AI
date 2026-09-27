"""
Traffic prediction model using Random Forest with uncertainty quantification.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
import joblib
import os
from src.ai.uncertainty import UncertaintyEstimator


class TrafficPredictor:
    """
    AI model predicting future traffic volume, queue length, and congestion level
    with ensemble variance for uncertainty quantification.
    """

    def __init__(self, n_estimators: int = 40, random_state: int = 42):
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=12,
            min_samples_split=4,
            random_state=random_state,
            n_jobs=-1,
        )
        self.uncertainty_estimator = UncertaintyEstimator(confidence_level=0.95)
        self.feature_names: List[str] = []
        self.target_names: List[str] = []
        self.is_trained: bool = False
        self.training_metrics: Dict[str, Dict[str, float]] = {}

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Train multi-target random forest model and evaluate metrics.
        """
        self.feature_names = list(X_train.columns)
        self.target_names = list(y_train.columns)

        self.model.fit(X_train, y_train)
        self.is_trained = True

        eval_X = X_val if X_val is not None else X_train
        eval_y = y_val if y_val is not None else y_train
        preds = self.model.predict(eval_X)

        metrics = {}
        for idx, target in enumerate(self.target_names):
            y_true = eval_y.iloc[:, idx]
            y_pred = preds[:, idx]
            metrics[target] = {
                "mae": round(float(mean_absolute_error(y_true, y_pred)), 3),
                "rmse": round(float(root_mean_squared_error(y_true, y_pred)), 3),
                "r2": round(float(r2_score(y_true, y_pred)), 3),
            }

        self.training_metrics = metrics
        return metrics

    def predict_single(
        self,
        features: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Predict for a single state vector with tree-based uncertainty intervals.
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before calling predict.")

        feat_vector = np.array([[features.get(f, 0.0) for f in self.feature_names]])

        # Multi-target ensemble tree predictions: list of length n_targets, each shape (n_estimators, 1)
        tree_preds_per_target = []
        for estimator in self.model.estimators_:
            # Each estimator outputs shape (1, n_targets)
            pred = estimator.predict(feat_vector)
            tree_preds_per_target.append(pred[0])

        tree_preds_array = np.array(tree_preds_per_target)  # shape (n_estimators, n_targets)

        results: Dict[str, Any] = {}
        for idx, target in enumerate(self.target_names):
            target_trees = tree_preds_array[:, idx]
            mean_val = float(np.mean(target_trees))
            std_val = float(np.std(target_trees))
            ci_margin = round(float(1.96 * std_val), 2)
            lower_bound = max(0.0, round(mean_val - ci_margin, 2))
            upper_bound = round(mean_val + ci_margin, 2)

            norm_uncertainty = min(1.0, max(0.05, (std_val / max(5.0, mean_val)) * 3.0))

            results[target] = {
                "prediction": round(mean_val, 2),
                "uncertainty_sigma": round(std_val, 2),
                "confidence_margin": ci_margin,
                "ci_lower": lower_bound,
                "ci_upper": upper_bound,
                "normalized_uncertainty": round(norm_uncertainty, 3),
            }

        return results

    def get_feature_importances(self) -> Dict[str, float]:
        """Return feature importance map sorted descending."""
        if not self.is_trained:
            return {}
        importances = self.model.feature_importances_
        return dict(
            sorted(
                {name: round(float(imp), 4) for name, imp in zip(self.feature_names, importances)}.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        )

    def save(self, filepath: str = "models/traffic_predictor.joblib"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names,
            "target_names": self.target_names,
            "metrics": self.training_metrics,
            "is_trained": self.is_trained,
        }, filepath)

    def load(self, filepath: str = "models/traffic_predictor.joblib"):
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.model = data["model"]
            self.feature_names = data["feature_names"]
            self.target_names = data["target_names"]
            self.training_metrics = data.get("metrics", {})
            self.is_trained = data.get("is_trained", True)
            return True
        return False
