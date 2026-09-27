"""
Unit tests for AI Preprocessing, Model Training, and Uncertainty Estimation.
"""

import pytest
import os
from src.ai.preprocessing import generate_synthetic_traffic_dataset, prepare_features_and_targets
from src.ai.predictor import TrafficPredictor
from src.ai.uncertainty import UncertaintyEstimator


def test_synthetic_data_generation(tmp_path):
    out_file = str(tmp_path / "test_traffic.csv")
    df = generate_synthetic_traffic_dataset(num_samples=80, num_intersections=4, output_path=out_file)
    assert os.path.exists(out_file)
    assert len(df) == 80 * 4
    assert "volume" in df.columns
    assert "queue_length" in df.columns


def test_ai_model_training_and_uncertainty(tmp_path):
    out_file = str(tmp_path / "test_traffic.csv")
    df = generate_synthetic_traffic_dataset(num_samples=100, num_intersections=4, output_path=out_file)
    X, y, f_cols, t_cols = prepare_features_and_targets(df)

    predictor = TrafficPredictor(n_estimators=10)
    metrics = predictor.train(X, y)

    assert "target_volume" in metrics
    assert metrics["target_volume"]["r2"] > 0.80

    sample = {col: X.iloc[0][col] for col in f_cols}
    pred_res = predictor.predict_single(sample)

    assert "target_volume" in pred_res
    vol_data = pred_res["target_volume"]
    assert vol_data["prediction"] > 0
    assert vol_data["confidence_margin"] > 0
    assert vol_data["ci_lower"] <= vol_data["prediction"] <= vol_data["ci_upper"]
