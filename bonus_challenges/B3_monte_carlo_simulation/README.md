# 🎲 Bonus Challenge B3 — 5-Year Monte Carlo NAV Simulation (+10 Marks)

## 📌 Overview
This module projects mutual fund Net Asset Value (NAV) trajectories over a **5-year forecast horizon** (1,260 trading days) using **5,000 simulated paths per fund**.

### 📐 Mathematical Formulation
Paths are generated via **Geometric Brownian Motion (GBM)** with Ito drift correction to guarantee expectation alignment:

$$\mu_{\text{adj}} = \mu_{\text{daily}} - \frac{1}{2}\sigma_{\text{daily}}^2$$

$$S_{t + \Delta t} = S_t \cdot \exp\left(\mu_{\text{adj}}\Delta t + \sigma_{\text{daily}}\sqrt{\Delta t} \cdot Z\right), \quad Z \sim \mathcal{N}(0, 1)$$

---

## 📊 Uncertainty Quantiles & Risk Cones
The simulation computes explicit confidence intervals at each trading day:
- **10th – 90th Percentile:** Represents the 80% confidence interval (extreme market downside vs. upside bull market).
- **25th – 75th Percentile:** Interquartile range (IQR) capturing central probability mass.
- **50th Percentile (Median):** Expected median compounding trajectory.

---

## 🚀 Execution

```bash
python bonus_challenges/B3_monte_carlo_simulation/monte_carlo_simulation.py
```

---

## 📁 Artifacts Included in this Folder
- [`monte_carlo_simulation.py`](file:///bonus_challenges/B3_monte_carlo_simulation/monte_carlo_simulation.py): Standalone simulation script.
- [`monte_carlo_projections.png`](file:///bonus_challenges/B3_monte_carlo_simulation/monte_carlo_projections.png): High-resolution plot with uncertainty bands and current NAV reference line.
- [`monte_carlo_summary.csv`](file:///bonus_challenges/B3_monte_carlo_simulation/monte_carlo_summary.csv): Quantitative summary table containing current NAV, annualized drift ($\mu$), volatility ($\sigma$), 5-year median NAV, and 10th/90th percentile bounds.
