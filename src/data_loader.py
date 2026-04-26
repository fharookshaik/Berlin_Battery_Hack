import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Paths
RAW_PATH = Path("/Users/fharook/Downloads/hackathon_deliverable/data/raw/project_A.xlsx")
PROCESSED_PATH = Path("/Users/fharook/Downloads/hackathon_deliverable/data/processed/project_A.parquet")
OUTPUTS_DIR = Path("/Users/fharook/Downloads/hackathon_deliverable/outputs")
METRICS_DIR = OUTPUTS_DIR / "metrics"
PLOTS_DIR = OUTPUTS_DIR / "plots"

# Create directories
METRICS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("PHASE 1: DATA LOADING & EXPLORATION - PROJECT A")
print("=" * 60)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================
# 1. LOAD DATA
# ============================================
print("[1/7] Loading project_A.xlsx ...")
df = pd.read_excel(RAW_PATH, sheet_name="data")
print(f"   → Loaded {len(df):,} rows")

# Timestamp is already datetime - just set as index
df = df.set_index('timestamp')
df = df.sort_index()

print(f"   → Time range: {df.index.min()} → {df.index.max()}")
print(f"   → Resolution: 15 minutes")

# ============================================
# 2. DATA INTEGRITY CHECKS
# ============================================
print("\n[2/7] Data Integrity Checks...")

checks = {
    "total_rows": len(df),
    "missing_values": df.isnull().sum().to_dict(),
    "duplicate_timestamps": df.index.duplicated().sum(),
    "time_range_days": (df.index.max() - df.index.min()).days,
    "expected_intervals": 35040,
    "actual_intervals": len(df),
    "gaps": 35040 - len(df)
}

print(f"   → Missing values: {sum(checks['missing_values'].values())} total")
print(f"   → Duplicate timestamps: {checks['duplicate_timestamps']}")
print(f"   → Gaps: {checks['gaps']}")

# ============================================
# 3. BASIC STATISTICS
# ============================================
print("\n[3/7] Basic Statistics...")

stats = df.describe().round(2)
print(stats)

# ============================================
# 4. NIGHT-TIME BEHAVIOR
# ============================================
print("\n[4/7] Night-time Behavior (Production == 0)...")

night_mask = df['production_kw'] == 0
night_hours = df[night_mask]
print(f"   → Night-time rows (production=0): {len(night_hours):,} ({len(night_hours)/len(df)*100:.1f}%)")
print(f"   → Night-time grid consumption mean: {night_hours['grid_consumption_kw'].mean():.2f} kW")
print(f"   → Night-time feed-in mean: {night_hours['feed_in_kw'].mean():.2f} kW")

# ============================================
# 5. PHYSICS CONSTRAINT CHECK
# ============================================
print("\n[5/7] Physics Constraint Check (both grid & feed-in > 0)...")

both_positive = (df['grid_consumption_kw'] > 0) & (df['feed_in_kw'] > 0)
both_count = both_positive.sum()
both_pct = both_count / len(df) * 100
print(f"   → Intervals with both > 0: {both_count:,} ({both_pct:.2f}%)")

# ============================================
# 6. ANNUAL TOTALS VERIFICATION
# ============================================
print("\n[6/7] Annual Totals Verification...")

annual = {
    "production_mwh": (df['production_kw'].sum() / 1000 / 4).round(2),  # kW → MWh (15min)
    "grid_consumption_mwh": (df['grid_consumption_kw'].sum() / 1000 / 4).round(2),
    "feed_in_mwh": (df['feed_in_kw'].sum() / 1000 / 4).round(2),
    "consumption_mwh": (df['consumption_kw'].sum() / 1000 / 4).round(2)
}

print(f"   → Production: {annual['production_mwh']} MWh")
print(f"   → Grid Consumption: {annual['grid_consumption_mwh']} MWh")
print(f"   → Feed-in: {annual['feed_in_mwh']} MWh")
print(f"   → Total Consumption: {annual['consumption_mwh']} MWh")

# Self-consumption ratio
self_consumed = annual['production_mwh'] - annual['feed_in_mwh']
sc_ratio = (self_consumed / annual['production_mwh'] * 100).round(1)
print(f"   → Calculated Self-Consumption Ratio: {sc_ratio}%")

# ============================================
# 7. SAVE PROCESSED DATA + REPORT
# ============================================
print("\n[7/7] Saving processed data and report...")

# Save processed data
df.to_parquet(PROCESSED_PATH)
print(f"   → Saved processed data to: {PROCESSED_PATH}")

# Save metrics
metrics = {
    "project": "A",
    "period": "2023 full year",
    "rows": len(df),
    "checks": checks,
    "annual_totals_mwh": annual,
    "self_consumption_ratio_calculated": sc_ratio,
    "both_grid_feedin_positive_pct": round(both_pct, 2),
    "night_production_zero_pct": round(len(night_hours)/len(df)*100, 1)
}

with open(METRICS_DIR / "phase1_data_quality.json", "w") as f:
    json.dump(metrics, f, indent=2, default=str)

print(f"   → Saved metrics to: {METRICS_DIR / 'phase1_data_quality.json'}")

print("\n" + "=" * 60)
print("PHASE 1 COMPLETED SUCCESSFULLY")
print("=" * 60)