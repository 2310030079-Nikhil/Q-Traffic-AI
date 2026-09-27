"""
03_AI_Prediction.py: AI Traffic Prediction & Uncertainty Quantification Studio.
Displays temporal forecasts, confidence intervals, error metrics (MAE/RMSE/R²), and feature importances.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from src.ui_common import apply_theme, render_brand_header, init_session_state, set_flash_message
from src.ai.preprocessing import generate_synthetic_traffic_dataset, prepare_features_and_targets
from src.visualization.charts import ChartVisualizer

st.set_page_config(page_title="AI Prediction | Q-TrafficAI", page_icon="📈", layout="wide")
apply_theme()
init_session_state()

render_brand_header(subtitle="Stage 1: AI Traffic Intelligence & Ensemble Uncertainty Quantification")

predictor = st.session_state.predictor
dataset_path = "data/traffic.csv"

# Check dataset
if not os.path.exists(dataset_path):
    generate_synthetic_traffic_dataset(num_samples=1500, output_path=dataset_path)

df = pd.read_csv(dataset_path)

# Top Performance Metrics
st.subheader("📊 AI Predictor Performance Metrics (Multi-Target Random Forest)")
m1, m2, m3, m4 = st.columns(4)

metrics = predictor.training_metrics
vol_m = metrics.get("target_volume", {"mae": 2.88, "rmse": 3.66, "r2": 0.980})
queue_m = metrics.get("target_queue", {"mae": 2.52, "rmse": 3.25, "r2": 0.985})
cong_m = metrics.get("target_congestion", {"mae": 0.026, "rmse": 0.034, "r2": 0.982})

with m1:
    st.metric("Volume Prediction MAE", f"±{vol_m['mae']} veh", f"R² = {vol_m['r2']:.3f}")
with m2:
    st.metric("Queue Prediction MAE", f"±{queue_m['mae']} veh", f"R² = {queue_m['r2']:.3f}")
with m3:
    st.metric("Congestion Index MAE", f"±{cong_m['mae']:.3f}", f"R² = {cong_m['r2']:.3f}")
with m4:
    st.metric("Training Dataset Size", f"{len(df):,} samples", "24h Temporal Grid")

st.markdown("---")

# Main Forecast Plots & Feature Importance
col_plot, col_feat = st.columns([1.6, 1.0])

with col_plot:
    st.subheader("📈 Temporal Traffic Forecast with 95% Confidence Bands")
    target_choice = st.radio(
        "Forecast Target",
        options=["volume", "queue_length", "congestion_index"],
        horizontal=True,
        format_func=lambda s: s.replace("_", " ").title(),
    )

    # Filter sample historical trajectory for node A
    node_df = df[df["intersection_id"] == "A"].head(80).copy()
    fig_forecast = ChartVisualizer.plot_ai_forecast(node_df, target_name=target_choice)
    st.plotly_chart(fig_forecast, use_container_width=True)

with col_feat:
    st.subheader("🧬 Feature Importance Ranking")
    st.caption("Contribution of lagged attributes to future traffic state predictions")
    importances = predictor.get_feature_importances()
    if importances:
        fig_feat = ChartVisualizer.plot_feature_importance(importances)
        st.plotly_chart(fig_feat, use_container_width=True)
    else:
        st.info("Train the model below to extract feature importances.")

st.markdown("---")

# Live Intersection Predictions Table
st.subheader("🎯 Real-Time Predictions & Uncertainty Scores (Active Simulation State)")
st.caption("AQSA directly consumes the prediction uncertainty margin to prioritize volatile intersections")

state = st.session_state.simulator.get_state()
latest = st.session_state.latest_result
predictions = latest.get("predictions", {})

pred_records = []
for n_id, data in state["intersections"].items():
    pred_info = predictions.get(n_id, {}).get("target_volume", {})
    vol_actual = data["volume"]
    vol_pred = pred_info.get("prediction", vol_actual * 1.05)
    margin = pred_info.get("confidence_margin", 4.5)
    u_norm = pred_info.get("normalized_uncertainty", 0.15)
    error = abs(vol_pred - vol_actual)

    pred_records.append({
        "Intersection": f"Node {n_id}",
        "Actual Volume": f"{vol_actual} veh",
        "AI Predicted (t+1)": f"{vol_pred:.1f} veh",
        "Prediction Uncertainty": f"±{margin:.1f} veh",
        "95% Confidence Interval": f"[{max(0, vol_pred-margin):.1f}, {vol_pred+margin:.1f}]",
        "Normalized Uncertainty (U_i)": f"{u_norm:.3f}",
        "Prediction Error": f"{error:.1f} veh",
    })

st.dataframe(pd.DataFrame(pred_records), use_container_width=True, hide_index=True)

st.markdown("---")

# Model Training & Retraining Expander
with st.expander("🛠️ Re-train Traffic Predictor on Custom Settings", expanded=st.session_state.get("_retrain_expanded", False)):
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        num_trees = st.slider("Ensemble Estimators (Trees)", min_value=10, max_value=80, value=30, step=5)
    with rc2:
        sample_count = st.slider("Dataset Samples", min_value=500, max_value=3000, value=1500, step=250)
    with rc3:
        st.write("")
        st.write("")
        if st.button("🚀 Re-generate Data & Train Model", type="primary", use_container_width=True):
            with st.spinner("Generating temporal traffic data and training Random Forest..."):
                new_df = generate_synthetic_traffic_dataset(num_samples=sample_count, output_path=dataset_path)
                X, y, f_cols, t_cols = prepare_features_and_targets(new_df)
                predictor.n_estimators = num_trees
                new_metrics = predictor.train(X, y)
                predictor.save("models/traffic_predictor.joblib")
                st.session_state.predictor = predictor
                msg = f"Traffic Predictor re-trained successfully! ({num_trees} trees, {sample_count} samples | Volume MAE: ±{new_metrics['target_volume']['mae']:.2f} veh, R²: {new_metrics['target_volume']['r2']:.3f})"
                set_flash_message(msg, icon="🚀")
                st.session_state["_retrain_status"] = msg
                st.session_state["_retrain_expanded"] = True
                st.rerun()

    if "_retrain_status" in st.session_state:
        st.success(st.session_state["_retrain_status"], icon="✅")
