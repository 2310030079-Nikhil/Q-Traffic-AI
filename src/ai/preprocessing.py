"""
Data preprocessing, feature engineering, and synthetic traffic dataset generation.
"""

from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import os


def generate_synthetic_traffic_dataset(
    num_samples: int = 1500,
    num_intersections: int = 4,
    output_path: str = "data/traffic.csv",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generates a realistic temporal traffic dataset with diurnal patterns,
    morning/evening rush hour peaks, and localized stochastic fluctuations.
    """
    np.random.seed(seed)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    records: List[Dict[str, Any]] = []
    node_names = [chr(65 + i) for i in range(num_intersections)]

    for t in range(num_samples):
        # Simulated time-of-day cycle (0 to 24 hours over dataset)
        hour = (t * 0.1) % 24.0
        time_sin = np.sin(2 * np.pi * hour / 24.0)
        time_cos = np.cos(2 * np.pi * hour / 24.0)

        # Diurnal rush hour multipliers (morning peak 8am, evening peak 6pm)
        morning_peak = np.exp(-((hour - 8.0) ** 2) / 3.0)
        evening_peak = np.exp(-((hour - 18.0) ** 2) / 4.0)
        base_demand = 30.0 + 45.0 * morning_peak + 50.0 * evening_peak

        for node in node_names:
            node_factor = 1.0 + 0.25 * (ord(node) - 65)  # slight variance across nodes
            noise = np.random.normal(0, 4.5)
            # Inject occasional traffic spikes
            spike = 25.0 if (t % 120 > 110 and node in ("A", "B")) else 0.0

            volume = max(5, int(base_demand * node_factor + noise + spike))
            capacity = 100
            occupancy = min(1.0, volume / capacity)

            # Queue builds up non-linearly with occupancy
            queue = max(0, int(volume * (0.2 + 0.6 * (occupancy**1.8)) + np.random.normal(0, 2)))
            avg_wait = max(2.0, float(queue * 0.85 + np.random.uniform(1.0, 5.0)))
            avg_speed = max(4.0, float(13.88 * (1.0 - 0.7 * occupancy) + np.random.normal(0, 0.5)))
            density = float(volume * 3.3)  # veh/km

            congestion = min(1.0, 0.45 * occupancy + 0.35 * (queue / capacity) + 0.20 * (avg_wait / 60.0))

            records.append({
                "timestep": t,
                "hour": round(hour, 2),
                "time_sin": round(time_sin, 4),
                "time_cos": round(time_cos, 4),
                "intersection_id": node,
                "volume": volume,
                "queue_length": queue,
                "avg_waiting_time": round(avg_wait, 2),
                "occupancy": round(occupancy, 3),
                "density": round(density, 1),
                "avg_speed": round(avg_speed, 2),
                "congestion_index": round(congestion, 3),
            })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    return df


def prepare_features_and_targets(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str], List[str]]:
    """
    Constructs lagged temporal features and prediction targets (next-step volume, queue, congestion).
    """
    df_sorted = df.sort_values(by=["intersection_id", "timestep"]).copy()

    feature_cols = [
        "time_sin", "time_cos", "volume", "queue_length",
        "avg_waiting_time", "occupancy", "density", "avg_speed", "congestion_index",
    ]

    # Create lag-1 features per intersection
    for col in ["volume", "queue_length", "congestion_index"]:
        df_sorted[f"{col}_lag1"] = df_sorted.groupby("intersection_id")[col].shift(1)
        feature_cols.append(f"{col}_lag1")

    # One-hot encode intersection_id
    id_dummies = pd.get_dummies(df_sorted["intersection_id"], prefix="node", dtype=float)
    df_sorted = pd.concat([df_sorted, id_dummies], axis=1)
    feature_cols.extend(id_dummies.columns.tolist())

    # Create future targets (t+1)
    df_sorted["target_volume"] = df_sorted.groupby("intersection_id")["volume"].shift(-1)
    df_sorted["target_queue"] = df_sorted.groupby("intersection_id")["queue_length"].shift(-1)
    df_sorted["target_congestion"] = df_sorted.groupby("intersection_id")["congestion_index"].shift(-1)

    target_cols = ["target_volume", "target_queue", "target_congestion"]

    clean_df = df_sorted.dropna()
    X = clean_df[feature_cols]
    y = clean_df[target_cols]

    return X, y, feature_cols, target_cols
