import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime

# Paths
RAW_PATH = Path("/Users/fharook/Downloads/hackathon_deliverable/data/raw/project_A.xlsx")
OUTPUTS_DIR = Path("/Users/fharook/Downloads/hackathon_deliverable/outputs")
RECON_DIR = OUTPUTS_DIR / "reconstructions"
PLOTS_DIR = OUTPUTS_DIR / "plots"
METRICS_DIR = OUTPUTS_DIR / "metrics"

# Create directories
RECON_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 65)
print("EASY MODE IMPLEMENTATION - PROJECT A")
print("=" * 65)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================
# 1. LOAD DATA DIRECTLY FROM RAW EXCEL
# ============================================
print("[1/6] Loading project_A.xlsx ...")
df = pd.read_excel(RAW_PATH, sheet_name="data")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df = df.sort_index()
print(f"   → Loaded {len(df):,} rows")

# ============================================
# 2. EASY MODE RECONSTRUCTION
# ============================================
print("\n[2/6] Applying Easy Mode reconstruction formula...")

# Physical formula: consumption = production + grid - feed_in
df['consumption_reconstructed'] = (
    df['production_kw'] + 
    df['grid_consumption_kw'] - 
    df['feed_in_kw']
)

# Round to 2 decimal places (realistic meter precision)
df['consumption_reconstructed'] = df['consumption_reconstructed'].round(2)

print("   → Formula applied: consumption = production + grid_consumption - feed_in")

# ============================================
# 3. ERROR ANALYSIS
# ============================================
print("\n[3/6] Calculating error metrics...")

# Calculate errors
df['error'] = df['consumption_reconstructed'] - df['consumption_kw']
df['abs_error'] = df['error'].abs()
df['pct_error'] = np.where(
    df['consumption_kw'] != 0,
    (df['abs_error'] / df['consumption_kw']) * 100,
    0
)

# Key metrics
mae = df['abs_error'].mean()
rmse = np.sqrt((df['error'] ** 2).mean())
mape = df['pct_error'].mean()
max_error = df['abs_error'].max()
r2 = 1 - (np.sum(df['error']**2) / np.sum((df['consumption_kw'] - df['consumption_kw'].mean())**2))

metrics = {
    "mode": "Easy",
    "project": "A",
    "mae_kw": round(mae, 3),
    "rmse_kw": round(rmse, 3),
    "mape_percent": round(mape, 2),
    "max_error_kw": round(max_error, 2),
    "r2_score": round(r2, 6),
    "mean_ground_truth_kw": round(df['consumption_kw'].mean(), 2),
    "mean_reconstructed_kw": round(df['consumption_reconstructed'].mean(), 2),
    "total_intervals": len(df),
    "overlap_intervals_both_positive": int(((df['grid_consumption_kw'] > 0) & (df['feed_in_kw'] > 0)).sum())
}

print(f"   → MAE:  {mae:.3f} kW")
print(f"   → RMSE: {rmse:.3f} kW")
print(f"   → MAPE: {mape:.2f}%")
print(f"   → R²:   {r2:.6f}")

# ============================================
# 4. ANNUAL ENERGY BALANCE CHECK
# ============================================
print("\n[4/6] Annual Energy Balance Validation...")

annual_recon = (df['consumption_reconstructed'].sum() / 1000 / 4).round(2)
annual_gt = (df['consumption_kw'].sum() / 1000 / 4).round(2)
balance_error = abs(annual_recon - annual_gt)

print(f"   → Ground Truth Annual Consumption: {annual_gt} MWh")
print(f"   → Reconstructed Annual Consumption: {annual_recon} MWh")
print(f"   → Difference: {balance_error:.2f} MWh ({balance_error/annual_gt*100:.4f}%)")

metrics["annual_consumption_gt_mwh"] = annual_gt
metrics["annual_consumption_recon_mwh"] = annual_recon
metrics["annual_balance_error_mwh"] = round(balance_error, 4)

# ============================================
# 5. SAVE RECONSTRUCTED DATA + METRICS
# ============================================
print("\n[5/6] Saving outputs...")

# Save full reconstructed dataframe (key columns)
recon_df = df[['production_kw', 'consumption_kw', 'consumption_reconstructed', 
               'feed_in_kw', 'grid_consumption_kw', 'error']].copy()
recon_df.to_csv(RECON_DIR / "easy_mode_reconstruction.csv", index=True)
print(f"   → Saved: {RECON_DIR / 'easy_mode_reconstruction.csv'}")

# Save metrics
with open(METRICS_DIR / "easy_mode_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
print(f"   → Saved: {METRICS_DIR / 'easy_mode_metrics.json'}")

# ============================================
# 6. VISUALIZATIONS
# ============================================
print("\n[6/6] Generating visualizations...")

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)

# Sample days for visualization
sample_dates = [
    '2023-06-15',  # Summer sunny day
    '2023-01-15',  # Winter day
    '2023-03-22',  # Spring day with variability
]

for date in sample_dates:
    day_df = df.loc[date]
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # Top: Production, Consumption (GT vs Recon), Feed-in
    axes[0].plot(day_df.index, day_df['production_kw'], label='Production (kW)', color='#f39c12', linewidth=2)
    axes[0].plot(day_df.index, day_df['consumption_kw'], label='Consumption Ground Truth', color='#2ecc71', linewidth=2)
    axes[0].plot(day_df.index, day_df['consumption_reconstructed'], label='Consumption Reconstructed (Easy)', 
                 color='#e74c3c', linewidth=2, linestyle='--')
    axes[0].plot(day_df.index, day_df['feed_in_kw'], label='Feed-in (kW)', color='#3498db', linewidth=1.5, alpha=0.7)
    axes[0].set_title(f'Easy Mode Reconstruction - {date}', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right')
    axes[0].set_ylabel('Power (kW)')
    
    # Bottom: Error
    axes[1].fill_between(day_df.index, 0, day_df['error'], alpha=0.3, color='red')
    axes[1].plot(day_df.index, day_df['error'], color='red', linewidth=1)
    axes[1].axhline(0, color='black', linestyle='--', linewidth=1)
    axes[1].set_ylabel('Reconstruction Error (kW)')
    axes[1].set_xlabel('Time')
    
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f"easy_mode_{date}.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   → Saved plot: easy_mode_{date}.png")

print("\n" + "=" * 65)
print("EASY MODE COMPLETED SUCCESSFULLY")
print("=" * 65)
print(f"\nFinal Metrics Summary:")
print(f"  MAE:  {mae:.3f} kW")
print(f"  RMSE: {rmse:.3f} kW")
print(f"  MAPE: {mape:.2f}%")
print(f"  R²:   {r2:.6f}")
print(f"\nAll outputs saved in /Users/fharook/Downloads/hackathon_deliverable/outputs/")