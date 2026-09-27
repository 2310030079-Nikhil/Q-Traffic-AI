"""
Common UI components, styling, session state management, branding headers, and architecture visualizer.
"""

from typing import Dict, Any, Optional
import streamlit as st
import os

from src.traffic.simulator import TrafficSimulator
from src.ai.predictor import TrafficPredictor
from src.aqsa.aqsa_pipeline import AQSAPipeline
from src.evaluation.comparison import AlgorithmComparator
from src.evaluation.experiments import ExperimentManager


CUSTOM_CSS = """
<style>
/* Import High-Impact Modern Fonts */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* Core Canvas Background & Cyber-Quantum Ambient Glow */
.stApp {
    background-color: #070b14;
    background-image: 
        radial-gradient(at 0% 0%, rgba(0, 242, 254, 0.05) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.05) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(0, 230, 118, 0.03) 0px, transparent 50%);
    background-attachment: fixed;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Modern Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px !important;
    color: #f8fafc !important;
}

p, span, label, div {
    font-family: 'Inter', sans-serif;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Metric Cards with Glowing Gradient Top Accent */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(13, 20, 36, 0.7) 100%) !important;
    border: 1px solid rgba(56, 189, 248, 0.22) !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    position: relative !important;
    overflow: hidden !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(12px) !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #00f2fe 0%, #38bdf8 40%, #a855f7 80%, #00e676 100%);
    opacity: 0.9;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-4px) !important;
    border-color: rgba(0, 242, 254, 0.55) !important;
    box-shadow: 0 16px 36px -4px rgba(0, 242, 254, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px !important;
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px !important;
}

/* Primary Action Buttons - High Impact Quantum Cyan */
button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"], button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #00f2fe 0%, #00c6ff 50%, #0077b6 100%) !important;
    color: #030816 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.96rem !important;
    border: none !important;
    border-radius: 9px !important;
    padding: 0.6rem 1.4rem !important;
    box-shadow: 0 4px 18px rgba(0, 242, 254, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    letter-spacing: 0.3px !important;
    cursor: pointer !important;
}

button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-2px) scale(1.015) !important;
    box-shadow: 0 8px 28px rgba(0, 242, 254, 0.68), inset 0 1px 0 rgba(255, 255, 255, 0.7) !important;
    color: #01040a !important;
}

button[kind="primary"]:active {
    transform: translateY(1px) scale(0.99) !important;
}

/* Secondary Action Buttons - Cyber Glassmorphism */
button[kind="secondary"], .stButton > button[data-testid="stBaseButton-secondary"], button[data-testid="baseButton-secondary"], .stButton > button {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.65) 100%) !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    border: 1px solid rgba(148, 163, 184, 0.25) !important;
    border-radius: 9px !important;
    padding: 0.55rem 1.2rem !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25) !important;
    transition: all 0.25s ease !important;
    cursor: pointer !important;
}

button[kind="secondary"]:hover, .stButton > button:hover {
    border-color: #00f2fe !important;
    color: #00f2fe !important;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.85) 100%) !important;
    box-shadow: 0 4px 20px rgba(0, 242, 254, 0.25) !important;
    transform: translateY(-2px) !important;
}

/* Brand Banner Styling */
.brand-banner {
    background: linear-gradient(135deg, rgba(7, 19, 41, 0.92) 0%, rgba(12, 32, 64, 0.85) 50%, rgba(7, 19, 41, 0.92) 100%);
    border: 1px solid rgba(0, 242, 254, 0.32);
    border-radius: 14px;
    padding: 22px 28px;
    margin-bottom: 24px;
    box-shadow: 0 12px 36px rgba(0, 242, 254, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(16px);
}

.brand-banner::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 320px;
    height: 320px;
    background: radial-gradient(circle, rgba(0, 242, 254, 0.12) 0%, transparent 70%);
    pointer-events: none;
}

.brand-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00f2fe 0%, #38bdf8 35%, #818cf8 70%, #00e676 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.8px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-subtitle {
    color: #94a3b8;
    font-size: 1.02rem;
    font-weight: 400;
    margin-bottom: 16px;
    line-height: 1.5;
}

.pipeline-steps {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 12px;
    align-items: center;
}

.pipeline-step {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(56, 189, 248, 0.28);
    padding: 7px 15px;
    border-radius: 8px;
    font-size: 0.84rem;
    font-weight: 700;
    color: #cbd5e1;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    transition: all 0.25s ease;
}

.pipeline-step:hover {
    border-color: #00f2fe;
    color: #ffffff;
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0, 242, 254, 0.25);
}

.step-arrow {
    color: #00f2fe;
    font-weight: 800;
    font-size: 1.1rem;
}

/* Glassmorphism Cards */
.glass-card {
    background: linear-gradient(145deg, rgba(15, 23, 42, 0.85) 0%, rgba(13, 20, 36, 0.7) 100%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(14px);
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: rgba(0, 242, 254, 0.45);
    box-shadow: 0 12px 36px rgba(0, 242, 254, 0.12);
}

.badge-quantum {
    background: rgba(0, 242, 254, 0.14);
    color: #00f2fe;
    border: 1px solid rgba(0, 242, 254, 0.4);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.3px;
    display: inline-block;
}

.badge-novelty {
    background: rgba(168, 85, 247, 0.18);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.45);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.3px;
    display: inline-block;
}

.badge-classical {
    background: rgba(148, 163, 184, 0.14);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.35);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    display: inline-block;
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #060911 !important;
    border-right: 1px solid rgba(30, 41, 59, 0.75) !important;
}

/* Streamlit Tabs Styling */
button[data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #94a3b8 !important;
    transition: all 0.2s ease !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #00f2fe !important;
    border-bottom-color: #00f2fe !important;
}

/* Streamlit Expanders Styling */
details[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.25s ease !important;
}

details[data-testid="stExpander"]:hover {
    border-color: rgba(0, 242, 254, 0.45) !important;
}

/* Streamlit Alert Styling */
div[data-testid="stAlert"] {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(13, 24, 44, 0.85) 100%) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(56, 189, 248, 0.32) !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35) !important;
    backdrop-filter: blur(12px) !important;
}

/* Dataframe and Table Polish */
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(30, 41, 59, 0.8) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35) !important;
}
</style>
"""


def apply_theme():
    """Inject custom styling into Streamlit application."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def set_flash_message(message: str, level: str = "success", icon: str = "✅"):
    """Queue a flash notification message to be displayed on the next render or rerun."""
    st.session_state["_flash_message"] = {
        "message": message,
        "level": level,
        "icon": icon,
    }


def render_flash_messages():
    """Render and consume any queued flash message using Streamlit alerts and toasts."""
    flash = st.session_state.pop("_flash_message", None)
    if flash:
        msg = flash.get("message", "")
        level = flash.get("level", "success")
        icon = flash.get("icon", "✅")
        if level == "success":
            st.success(msg, icon=icon)
        elif level == "info":
            st.info(msg, icon=icon)
        elif level == "warning":
            st.warning(msg, icon=icon)
        elif level == "error":
            st.error(msg, icon=icon)

        try:
            st.toast(msg, icon=icon)
        except Exception:
            pass


def render_sidebar_telemetry():
    """Render live quantum engine status and telemetry in the sidebar."""
    with st.sidebar:
        st.markdown("---")
        sim = st.session_state.get("simulator")
        latest = st.session_state.get("latest_result")

        sim_step = sim.step_count if sim else 0
        sim_time = f"{sim.time:.1f}s" if sim else "0.0s"
        scenario = sim.scenario.replace("_", " ").title() if sim else "Morning Peak"
        qubits = latest["selection"]["num_qubits"] if latest else 6
        depth = latest["qaoa"]["circuit_depth"] if latest else 1

        st.markdown(f"""
        <div style="background:linear-gradient(145deg, #091326 0%, #0d213f 100%); border:1px solid rgba(0, 242, 254, 0.28); border-radius:10px; padding:14px; box-shadow:0 4px 15px rgba(0, 242, 254, 0.08);">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
                <span style="font-size:0.75rem; font-weight:700; color:#00f2fe; letter-spacing:0.8px; text-transform:uppercase;">Quantum Engine</span>
                <span style="display:inline-flex; align-items:center; gap:5px; font-size:0.72rem; color:#00e676; background:rgba(0, 230, 118, 0.12); padding:2px 8px; border-radius:10px; border:1px solid rgba(0, 230, 118, 0.3);">
                    <span style="width:6px; height:6px; border-radius:50%; background:#00e676; box-shadow:0 0 8px #00e676;"></span> ONLINE
                </span>
            </div>
            <div style="font-size:0.8rem; color:#94a3b8; line-height:1.65;">
                <div>⚡ <b>Backend:</b> Qiskit Aer (Local)</div>
                <div>⚛ <b>Qubits Allocated:</b> <span style="color:#00f2fe; font-weight:600;">{qubits} Qubits</span> (p={depth})</div>
                <div>🚗 <b>Scenario:</b> <span style="color:#f8fafc;">{scenario}</span></div>
                <div>⏱ <b>Sim Clock:</b> <span style="color:#38bdf8;">{sim_time}</span> (Step #{sim_step})</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Q-TrafficAI v2.4 | Academic Major Project")


def render_brand_header(subtitle: str = "Adaptive Quantum Signal Allocation for AI-Driven Intelligent Traffic Optimization"):
    """Render top branding banner with four-stage pipeline indicator and active flash alerts."""
    st.markdown(f"""
    <div class="brand-banner">
        <div class="brand-title">⚛ Q-TrafficAI</div>
        <div class="brand-subtitle"><b>Think Ahead. Optimize Smarter. Move Faster.</b> | {subtitle}</div>
        <div class="pipeline-steps">
            <span class="pipeline-step"><span style="color:#00f2fe;">●</span> 1. AI PREDICTS</span>
            <span class="step-arrow">→</span>
            <span class="pipeline-step"><span style="color:#38bdf8;">●</span> 2. AQSA SELECTS</span>
            <span class="step-arrow">→</span>
            <span class="pipeline-step"><span style="color:#a855f7;">●</span> 3. QUANTUM OPTIMIZES</span>
            <span class="step-arrow">→</span>
            <span class="pipeline-step"><span style="color:#00e676;">●</span> 4. TRAFFIC IMPROVES</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    render_flash_messages()
    render_sidebar_telemetry()


def render_architecture_flow():
    """Render a visually stunning, high-definition interactive diagram of the 8-stage AQSA pipeline."""
    st.markdown("""
    <div style="background:linear-gradient(145deg, #091326 0%, #0d213f 100%); border:1px solid rgba(0, 242, 254, 0.25); border-radius:12px; padding:20px; box-shadow:0 8px 30px rgba(0, 0, 0, 0.4);">
        <div style="display:flex; flex-direction:column; gap:10px;">
            
            <!-- Step 1 -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(15, 23, 42, 0.85); border:1px solid rgba(56, 189, 248, 0.2); border-radius:8px; padding:10px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:rgba(0, 242, 254, 0.15); color:#00f2fe; border-radius:6px; padding:4px 8px; font-weight:700; font-size:0.8rem;">01</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.92rem;">📡 Smart City Traffic Network Sensors</div>
                        <div style="font-size:0.78rem; color:#94a3b8;">Extracts real-time queue lengths, approach wait times, velocity & road occupancy</div>
                    </div>
                </div>
                <span class="badge-classical">Data Acquisition</span>
            </div>

            <div style="text-align:center; color:#00f2fe; font-size:0.9rem; line-height:1;">↓</div>

            <!-- Step 2 -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(15, 23, 42, 0.85); border:1px solid rgba(129, 140, 248, 0.25); border-radius:8px; padding:10px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:rgba(129, 140, 248, 0.15); color:#818cf8; border-radius:6px; padding:4px 8px; font-weight:700; font-size:0.8rem;">02</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.92rem;">🤖 AI Traffic Forecaster + Uncertainty Quantification</div>
                        <div style="font-size:0.78rem; color:#94a3b8;">Random Forest ensembles predict t+1 demand and 95% confidence interval margin U_i</div>
                    </div>
                </div>
                <span class="badge-classical">AI Ensemble</span>
            </div>

            <div style="text-align:center; color:#c084fc; font-size:0.9rem; line-height:1;">↓</div>

            <!-- Step 3 (Novelty) -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:linear-gradient(90deg, rgba(168, 85, 247, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%); border:1px solid rgba(168, 85, 247, 0.45); border-radius:8px; padding:12px 14px; box-shadow:0 0 16px rgba(168, 85, 247, 0.12);">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:#a855f7; color:#ffffff; border-radius:6px; padding:4px 8px; font-weight:800; font-size:0.8rem;">03</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.95rem;">⭐ AQSA Signal Priority Scoring (Dynamic Weights)</div>
                        <div style="font-size:0.8rem; color:#cbd5e1; font-family:'JetBrains Mono', monospace;">P_i = w1(t)*C_i + w2(t)*Q_i + w3(t)*W_i + w4(t)*D_i + w5(t)*U_i</div>
                    </div>
                </div>
                <span class="badge-novelty">★ Core Novelty</span>
            </div>

            <div style="text-align:center; color:#c084fc; font-size:0.9rem; line-height:1;">↓</div>

            <!-- Step 4 (Novelty) -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:linear-gradient(90deg, rgba(168, 85, 247, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%); border:1px solid rgba(168, 85, 247, 0.45); border-radius:8px; padding:12px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:#a855f7; color:#ffffff; border-radius:6px; padding:4px 8px; font-weight:800; font-size:0.8rem;">04</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.95rem;">⚛ Adaptive Quantum Variable Selection & Qubit Budget Mapping</div>
                        <div style="font-size:0.78rem; color:#cbd5e1;">Filters nodes exceeding cutoff τ; maps highest-priority bottlenecks to active qubits B</div>
                    </div>
                </div>
                <span class="badge-novelty">★ Core Novelty</span>
            </div>

            <div style="text-align:center; color:#00f2fe; font-size:0.9rem; line-height:1;">↓</div>

            <!-- Step 5 (Novelty) -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:linear-gradient(90deg, rgba(0, 242, 254, 0.12) 0%, rgba(15, 23, 42, 0.9) 100%); border:1px solid rgba(0, 242, 254, 0.35); border-radius:8px; padding:12px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:#00f2fe; color:#040d1a; border-radius:6px; padding:4px 8px; font-weight:800; font-size:0.8rem;">05</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.95rem;">🧩 Dynamic QUBO Matrix Assembly & Adaptive Conflict Penalties</div>
                        <div style="font-size:0.78rem; color:#cbd5e1;">Injects arterial green-wave rewards and dynamically scales penalty λ_i based on priority P_i</div>
                    </div>
                </div>
                <span class="badge-novelty">★ Core Novelty</span>
            </div>

            <div style="text-align:center; color:#00f2fe; font-size:0.9rem; line-height:1;">↓</div>

            <!-- Step 6 (Quantum) -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(15, 23, 42, 0.85); border:1px solid rgba(0, 242, 254, 0.35); border-radius:8px; padding:10px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:rgba(0, 242, 254, 0.2); color:#00f2fe; border-radius:6px; padding:4px 8px; font-weight:700; font-size:0.8rem;">06</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.92rem;">🌀 QAOA Quantum Circuit Execution (Qiskit Aer Simulator)</div>
                        <div style="font-size:0.78rem; color:#94a3b8;">Alternates cost and mixer unitaries e^{-iβ H_M} e^{-iγ H_C} with classical COBYLA optimizer</div>
                    </div>
                </div>
                <span class="badge-quantum">Quantum Solver</span>
            </div>

            <div style="text-align:center; color:#00e676; font-size:0.9rem; line-height:1;">↓</div>

            <!-- Step 7 (Novelty) -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:linear-gradient(90deg, rgba(0, 230, 118, 0.12) 0%, rgba(15, 23, 42, 0.9) 100%); border:1px solid rgba(0, 230, 118, 0.35); border-radius:8px; padding:12px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:#00e676; color:#040d1a; border-radius:6px; padding:4px 8px; font-weight:800; font-size:0.8rem;">07</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.95rem;">🛡️ Feasibility-Aware Quantum Decoder</div>
                        <div style="font-size:0.78rem; color:#cbd5e1;">Discards infeasible conflict bitstrings, ensuring 100% collision-free phase allocations</div>
                    </div>
                </div>
                <span class="badge-novelty">★ Core Novelty</span>
            </div>

            <div style="text-align:center; color:#00e676; font-size:0.9rem; line-height:1;">↓</div>

            <!-- Step 8 -->
            <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(15, 23, 42, 0.85); border:1px solid rgba(0, 230, 118, 0.25); border-radius:8px; padding:10px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:rgba(0, 230, 118, 0.2); color:#00e676; border-radius:6px; padding:4px 8px; font-weight:700; font-size:0.8rem;">08</span>
                    <div>
                        <div style="font-weight:700; color:#f8fafc; font-size:0.92rem;">🚦 Physical Signal Actuation & Closed-Loop Telemetry</div>
                        <div style="font-size:0.78rem; color:#94a3b8;">Deploys optimal green splits to city controllers and advances discrete simulation</div>
                    </div>
                </div>
                <span class="badge-classical">Closed Loop</span>
            </div>

        </div>
    </div>
    """, unsafe_allow_html=True)


def init_session_state():
    """Ensure persistent simulation, model, and pipeline objects are instantiated."""
    if "simulator" not in st.session_state:
        st.session_state.simulator = TrafficSimulator(num_intersections=4, scenario="morning_peak", seed=42)
        # Advance 6 steps for realistic initial congestion
        for _ in range(6):
            st.session_state.simulator.step()

    if "predictor" not in st.session_state:
        pred = TrafficPredictor()
        model_path = "models/traffic_predictor.joblib"
        if os.path.exists(model_path):
            pred.load(model_path)
        st.session_state.predictor = pred

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = AQSAPipeline(
            predictor=st.session_state.predictor,
            threshold=0.55,
            qubit_budget=6,
            qaoa_depth=1,
            shots=512,
        )

    if "latest_result" not in st.session_state:
        # Run initial baseline optimization pass
        state = st.session_state.simulator.get_state()
        st.session_state.latest_result = st.session_state.pipeline.run(state)

    if "comparator" not in st.session_state:
        st.session_state.comparator = AlgorithmComparator(predictor=st.session_state.predictor)

    if "exp_manager" not in st.session_state:
        st.session_state.exp_manager = ExperimentManager(predictor=st.session_state.predictor)
