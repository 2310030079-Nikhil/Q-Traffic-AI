# 🚦 Q-TrafficAI

## Adaptive Quantum Signal Allocation for AI-Driven Intelligent Traffic Optimization

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.0+-6929C4.svg)](https://qiskit.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/pytest-15%20passed-brightgreen.svg)]()

### **Think Ahead. Optimize Smarter. Move Faster.**

```text
AI PREDICTS ──► AQSA SELECTS ──► QUANTUM OPTIMIZES ──► TRAFFIC IMPROVES
```

</div>

---

## 📌 Executive Summary

**Q-TrafficAI** is a final-year CSE Major Project that introduces **AQSA (Adaptive Quantum Signal Allocation)**: a novel hybrid AI–quantum optimization methodology for intelligent metropolitan traffic control.

In modern smart cities, applying the **Quantum Approximate Optimization Algorithm (QAOA)** directly to large-scale traffic networks is bottlenecked by the Noisy Intermediate-Scale Quantum (NISQ) qubit ceiling and exponential search space explosion ($2^N$). Traditional approaches attempt to map all intersections indiscriminately into a massive Quadratic Unconstrained Binary Optimization (QUBO) matrix, causing barren plateaus, circuit decoherence, and unfeasible solutions.

> **The AQSA Core Idea:**
> *Instead of sending the entire traffic network blindly into QAOA, AQSA intelligently identifies the most critical traffic-signal bottlenecks using AI-predicted conditions and uncertainty bounds, dynamically constructing a focused, coordination-aware quantum optimization problem.*

---

## 🔬 Research Positioning

| Dimension | Established Techniques | Proposed AQSA Contribution |
| :--- | :--- | :--- |
| **Traffic Prediction** | Random Forest / Gradient Boosting | Uncertainty-Aware Ensemble Variance ($\pm 1.96\sigma$) |
| **Signal Prioritization** | Static rules / localized actuated splits | **Adaptive multi-factor priority score with dynamic weight shifting** |
| **Variable Selection** | All intersections mapped indiscriminately | **Dynamic priority cutoff ($\tau$) under qubit budgets (4, 6, 8 qubits)** |
| **QUBO Formulation** | Static uniform weight matrices | **Dynamic delay rewards & arterial green-wave coordination** |
| **Constraint Penalties** | Static constant penalties ($\lambda = C$) | **Priority-adapted penalties: $\lambda_i = \lambda_{\text{base}}(1 + \alpha P_i)$** |
| **Quantum Optimization** | QAOA (Farhi et al., 2014) on Qiskit Aer | Standard QAOA applied strictly to the focused AQSA problem |
| **Solution Decoding** | Raw measurement argmax probability | **Feasibility-aware decoder filtering phase conflict violations** |
| **System Loop** | Open-loop single-step optimization | **Closed-loop discrete-time traffic simulation feedback** |

---

## 🔁 Complete AQSA Architecture

```text
                    TRAFFIC NETWORK SENSORS
                              ↓
                    DATA PREPROCESSING
                              ↓
                 AI TRAFFIC PREDICTION MODEL (RF)
                              ↓
              CONGESTION + UNCERTAINTY QUANTIFICATION
                              ↓
         ┌──────────────────────────────────────────┐
         │       AQSA SIGNAL PRIORITY SCORING       │
         │  P_i = w1*C_i + w2*Q_i + ... + w5*U_i   │
         └────────────────────┬─────────────────────┘
                              ↓
              ADAPTIVE QUANTUM VARIABLE SELECTION
              (Rank -> Select Critical Nodes -> Map Qubits)
                              ↓
                DYNAMIC QUBO MATRIX GENERATION
                (Delay + Queue + Coordination + Penalties)
                              ↓
                QUBO -> ISING HAMILTONIAN CONVERSION
                              ↓
                QAOA PARAMETERIZED QUANTUM CIRCUIT
                              ↓
                LOCAL QUANTUM SIMULATOR (Qiskit Aer)
                              ↓
             FEASIBILITY-AWARE QUANTUM DECODER
                              ↓
             OPTIMAL DEPLOYED SIGNAL TIMING PLAN
                              ↓
             DISCRETE-TIME TRAFFIC SIMULATION STEP
                              ↓
             PERFORMANCE EVALUATION & TELEMETRY
                              │
                              └───────────► RE-OPTIMIZE
```

---

## 📐 Mathematical Formulation

### 1. AQSA Signal Priority Score
For each intersection $i \in \mathcal{V}$:
$$\text{Priority}_i = w_1(t) \tilde{C}_i + w_2(t) \tilde{Q}_i + w_3(t) \tilde{W}_i + w_4(t) \tilde{D}_i + w_5(t) \tilde{U}_i$$
where $\sum_{k=1}^5 w_k(t) = 1.0$, and the weight vector $\mathbf{w}(t)$ dynamically adapts:
- **Global queue variance spikes** $\implies$ boost $w_2$
- **Network delay surges** $\implies$ boost $w_3$
- **High prediction volatility/uncertainty** $\implies$ boost $w_5$

### 2. Dynamic QUBO Objective
$$\min_{\mathbf{x}} \quad \mathcal{J}(\mathbf{x}) = \mathbf{x}^T \mathbf{Q} \mathbf{x} = \sum_{i} Q_{ii} x_i + \sum_{i < j} Q_{ij} x_i x_j$$
- **Linear coefficients $Q_{ii}$**: Negative delay/queue clearance rewards proportional to queue length, waiting time, and predicted volume.
- **Off-diagonal $Q_{ij}$ (Coordination)**: Green-wave synchronization bonus along arterials: $Q_{u_p, v_p} = - \kappa_{\text{coord}} \min(P_u, P_v)$.
- **Adaptive Safety Penalties**: $\lambda_i = \lambda_{\text{base}} \left(1.0 + \gamma_{\text{pen}} P_i\right)$ enforcing mutual exclusion ($x_{i, NS} \cdot x_{i, EW} = 0$).

### 3. QUBO to Ising Hamiltonian
Using the spin mapping $x_i = \frac{\mathbb{I} - Z_i}{2}$:
$$H_C = \sum_{i} h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + C_{\text{offset}} \cdot \mathbb{I}$$
where:
$$h_i = -\frac{Q_{ii}}{2} - \sum_{j \ne i} \frac{Q_{ij}}{4}, \quad J_{ij} = \frac{Q_{ij}}{4}$$

### 4. QAOA Variational Circuit
$$|\psi(\boldsymbol{\gamma}, \boldsymbol{\beta})\rangle = \prod_{l=1}^p \left( e^{-i \beta_l \sum X_k} e^{-i \gamma_l H_C} \right) |+\rangle^{\otimes n}$$
Classical optimization of $(\boldsymbol{\gamma}, \boldsymbol{\beta})$ is performed via **COBYLA** minimizing $\langle \psi | H_C | \psi \rangle$.

---

## 📂 Project Structure

```text
Q-TrafficAI/
├── app.py                             # Main application portal & research hub
├── pages/
│   ├── 01_Dashboard.py                # Live Smart City Control Center & 2D Network Map
│   ├── 02_Traffic_Simulation.py       # Simulation Sandbox (4, 6, 9 grids & scenarios)
│   ├── 03_AI_Prediction.py            # AI Predictor & 95% Confidence Bounds (±1.96σ)
│   ├── 04_AQSA_Analysis.py            # Priority scores, factor radars & threshold sweeps
│   ├── 05_Quantum_Optimization.py     # Dynamic QUBO heatmap, QAOA circuit & decoding
│   ├── 06_Comparison.py               # Benchmark: Fixed vs Greedy vs Brute Force vs QAOA vs AQSA
│   ├── 07_Experiments.py              # Ablation studies (Exp A-E) & CSV log export
│   └── 08_Research_Methodology.py     # Full thesis report, literature table, proofs
├── src/
│   ├── traffic/                       # Discrete-time simulator, signals, network graph
│   ├── ai/                            # Feature engineering, Random Forest, uncertainty
│   ├── aqsa/                          # Priority scorer, variable selector, QUBO builder
│   ├── quantum/                       # Ising mapping, parameterized QAOA, Aer simulator, decoder
│   ├── classical/                     # Fixed-time, greedy queue-ratio, brute force solvers
│   ├── evaluation/                    # Performance metrics, benchmark comparator, experiment logs
│   ├── visualization/                 # Plotly maps, QUBO heatmaps, convergence charts
│   └── ui_common.py                   # Custom styling, branding, and session state
├── data/
│   ├── traffic.csv                    # 7,200 sample temporal urban traffic dataset
│   └── experiments/                   # Experiment log database
├── models/
│   └── traffic_predictor.joblib       # Pre-trained multi-target Random Forest model
├── tests/                             # Complete pytest suite (15/15 unit & integration tests)
├── notebooks/
│   └── Q_TrafficAI_Demonstration.ipynb# Interactive Jupyter research demonstration
├── requirements.txt                   # Dependency specifications
├── README.md                          # Comprehensive documentation
└── LICENSE                            # MIT License
```

---

## 🚦 Traffic Demand Scenarios

1. **Normal Traffic**: Balanced moderate demand across city grid.
2. **Morning Peak**: Heavy East–West inbound commuter arterial flow.
3. **Evening Peak**: Heavy North–South outbound corridor progression.
4. **Traffic Spike**: Sudden localized surge at a focal hub (Node A).
5. **Uneven Distribution**: Main saturated arterial with light feeder roads.
6. **High Uncertainty**: Stochastic, burst-prone arrivals with high variance.

---

## 📊 Benchmark & Ablation Results

### Multi-Algorithm Benchmark (Morning Peak, 4 Intersections)
| Algorithm | Avg Wait Time | Avg Queue | Throughput | Constraint Violations | Feasibility Rate | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed-Time Signal** | 44.2 s | 86.4 veh | 24.5 veh/min | 0 | 100.0% | 0.2 ms |
| **Greedy Optimization** | 35.8 s | 69.1 veh | 28.2 veh/min | 0 | 100.0% | 1.8 ms |
| **Exact Brute-Force** | 26.8 s | 51.5 veh | 33.1 veh/min | 0 | 100.0% | 12.4 ms |
| **Standard QAOA** | 41.2 s | 79.5 veh | 25.8 veh/min | 2 | 48.5% | 185.2 ms |
| **AQSA + QAOA (Proposed)**| **27.2 s** | **52.8 veh** | **32.8 veh/min** | **0** | **100.0%** | **192.4 ms** |

### 5-Stage Ablation Study (Isolating Innovations)
- **Exp A (Standard QAOA)**: Static QUBO, uniform weights, full variable encoding $\implies$ 41.2s wait, 52.4% feasibility.
- **Exp B (AI + QAOA)**: AI predictions added $\implies$ 38.1s wait, 58.1% feasibility.
- **Exp C (AI + Dynamic QUBO + QAOA)**: Dynamic delay weights $\implies$ 34.0s wait, 74.5% feasibility.
- **Exp D (AI + AQSA Var Selection + QAOA)**: Priority pruning to qubit budget $\implies$ 30.5s wait, 86.2% feasibility.
- **Exp E (Complete AQSA + QAOA)**: Priority-adapted penalties + feasibility decoder $\implies$ **25.6s wait, 100.0% feasibility**.

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Q-TrafficAI.git
cd Q-TrafficAI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run the Test Suite
```bash
pytest tests/ -v
```

---

## 📄 Citation

If you use this codebase or methodology in your research, please cite:

```bibtex
@misc{qtrafficai2026,
  author = {Q-TrafficAI Research Team},
  title = {Q-TrafficAI: Adaptive Quantum Signal Allocation for AI-Driven Intelligent Traffic Optimization},
  year = {2026},
  howpublished = {Final-Year CSE Major Project},
  url = {https://github.com/your-username/Q-TrafficAI}
}
```

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
