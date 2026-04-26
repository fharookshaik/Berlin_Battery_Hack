**✅ PROJECT A – Complete Checklist**

### Phase 1: Data Loading & Exploration

- [ ] Load `project_A.xlsx` completely (all 35,040 rows)
- [ ] Verify data integrity (no missing timestamps, correct dtypes, timestamp as datetime)
- [ ] Quick sanity check: confirm annual totals match summary (Production 103.11 MWh, etc.)
- [ ] Explore basic statistics (min, max, mean, median per column)
- [ ] Identify night-time periods (production == 0) and confirm behavior
- [ ] Check % of intervals where both `grid_consumption > 0` and `feed_in > 0`
- [ ] Create initial data quality report

---

### Phase 2: Easy Mode Implementation

- [ ] Implement reconstruction logic for `consumption_kw`
- [ ] Handle edge cases (intervals where grid + feed-in both > 0)
- [ ] Apply the formula: `consumption = production - feed_in + grid_consumption`
- [ ] Run reconstruction on full dataset
- [ ] Compare reconstructed `consumption` vs ground truth
- [ ] Calculate error metrics (MAE, RMSE, MAPE, Max Error)
- [ ] Validate annual energy balance

---

### Phase 3: Hard Mode Implementation

- [ ] Implement reconstruction logic using only:
  - `grid_consumption_kw`
  - `production_kw`
  - Annual self-consumption ratio (37.5%)
- [ ] Use physics constraint: `grid > 0 → feed_in ≈ 0`
- [ ] Develop method to estimate `feed_in_kw` and `consumption_kw`
- [ ] Enforce annual self-consumption target
- [ ] Run reconstruction on full dataset
- [ ] Compare both reconstructed series vs ground truth
- [ ] Calculate error metrics (MAE, RMSE, MAPE for both consumption and feed-in)
- [ ] Validate annual energy balance and self-consumption ratio

---

### Phase 4: Validation & Metrics

- [ ] Create comparison DataFrame (Ground Truth vs Easy vs Hard)
- [ ] Calculate comprehensive error metrics table
- [ ] Analyze error distribution (histograms, boxplots)
- [ ] Identify worst-performing periods (e.g., morning ramp-up, cloudy days)
- [ ] Check physics violations in reconstructed data
- [ ] Document reconstruction accuracy summary

---

### Phase 5: Visualizations (Minimum Required)

- [ ] **Daily profile plots** (3–5 representative days: sunny summer, winter, cloudy, weekend)
- [ ] **Weekly heatmap** (consumption + feed-in + surplus)
- [ ] **Monthly bar charts** (self-consumption ratio, autarky, feed-in)
- [ ] **Error distribution plots** (Easy vs Hard mode)
- [ ] **Energy balance Sankey or stacked bar** (annual)
- [ ] **Surplus vs Deficit timeline** (highlight hidden periods)
- [ ] **Battery SOC simulation** (with vs without battery)

---

### Phase 6: Battery Simulation

- [ ] Define simple battery model (e.g., 80 kWh usable / 40 kW power)
- [ ] Run simulation using **Ground Truth** profiles
- [ ] Run simulation using **Easy Mode** reconstructed profiles
- [ ] Run simulation using **Hard Mode** reconstructed profiles
- [ ] Calculate key metrics for all three scenarios:
  - Self-consumption ratio (with battery)
  - Autarky
  - Grid import reduction (%)
  - Feed-in reduction (%)
  - Annual battery cycles
- [ ] Create comparison table + visualization

---

### Phase 7: Documentation & Final Deliverables

- [ ] Write short methodology explanation (Easy mode + Hard mode)
- [ ] Create final summary report (accuracy, limitations, recommendations)
- [ ] Prepare clean Jupyter Notebook (or Python script) with all steps
- [ ] Export key results (reconstructed DataFrames, metrics, plots)
- [ ] Document lessons learned and next steps for other projects

---

### Output Checklist (What We Must Deliver)

| # | Output | Format | Status |
|---|--------|--------|--------|
| 1 | Reconstructed `consumption_kw` (Easy Mode) | DataFrame / CSV | ☐ |
| 2 | Reconstructed `consumption_kw` + `feed_in_kw` (Hard Mode) | DataFrame / CSV | ☐ |
| 3 | Error Metrics Table (Easy vs Hard vs Ground Truth) | Table / Markdown | ☐ |
| 4 | Daily Profile Comparison Plots (Ground Truth vs Reconstructed) | PNG / Interactive HTML | ☐ |
| 5 | Battery Simulation Results Comparison | Table + Chart | ☐ |
| 6 | Energy Balance Validation (Annual) | Chart + Numbers | ☐ |
| 7 | Final Summary Report | Markdown / PDF | ☐ |
| 8 | Clean, well-commented code/notebook | `.ipynb` or `.py` | ☐ |
| 9 | Key insights & limitations document | Markdown | ☐ |

---
