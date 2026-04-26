import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime

# Paths
RAW_PATH = Path("/Users/fharook/Downloads/hackathon_deliverable/data/raw/project_A.xlsx")
RECON_DIR = Path("/Users/fharook/Downloads/hackathon_deliverable/outputs/reconstructions")
PLOTS_DIR = Path("/Users/fharook/Downloads/hackathon_deliverable/outputs/plots")

print("=" * 70)
print("PHASE 7: PDF-STYLE BATTERY VISUALIZATIONS")
print("=" * 70)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================
# LOAD DATA
# ============================================
print("[1/4] Loading data...")

df_gt = pd.read_excel(RAW_PATH, sheet_name="data")
df_gt['timestamp'] = pd.to_datetime(df_gt['timestamp'])
df_gt = df_gt.set_index('timestamp').sort_index()

df_easy = pd.read_csv(RECON_DIR / "easy_mode_reconstruction.csv", index_col=0, parse_dates=True)
df_xgb = pd.read_csv(RECON_DIR / "hard_mode_xgboost.csv", index_col=0, parse_dates=True)

# Merge all data
df = df_gt.copy()
df['consumption_easy'] = df_easy['consumption_reconstructed']
df['feed_in_xgb'] = df_xgb['feed_in_xgb']
df['consumption_xgb'] = df_xgb['consumption_xgb']

print("   → Data loaded and merged")

# ============================================
# BATTERY SIMULATION (reuse from Phase 6)
# ============================================
def run_battery_simulation(df, consumption_col, production_col):
    """Simple battery simulation"""
    BATTERY_CAPACITY = 80.0
    BATTERY_POWER = 40.0
    EFFICIENCY = 0.95
    
    surplus = (df[production_col] - df[consumption_col]).clip(lower=0)
    deficit = (df[consumption_col] - df[production_col]).clip(lower=0)
    
    soc = 0.0
    soc_list = []
    grid_remaining = []
    feedin_remaining = []
    
    for i in range(len(df)):
        s = surplus.iloc[i]
        d = deficit.iloc[i]
        
        charge = min(s * EFFICIENCY, BATTERY_POWER, BATTERY_CAPACITY - soc)
        soc += charge
        
        discharge = min(d, BATTERY_POWER, soc)
        soc -= discharge
        
        soc_list.append(soc)
        
        remaining_deficit = max(0, d - discharge)
        remaining_surplus = max(0, s - (charge / EFFICIENCY))
        
        grid_remaining.append(remaining_deficit)
        feedin_remaining.append(remaining_surplus)
    
    return pd.Series(soc_list, index=df.index), pd.Series(grid_remaining, index=df.index), pd.Series(feedin_remaining, index=df.index)

# Run simulations
print("[2/4] Running battery simulations for all scenarios...")

# Ground Truth
soc_gt, grid_rem_gt, feedin_rem_gt = run_battery_simulation(df, 'consumption_kw', 'production_kw')

# Easy Mode
soc_easy, grid_rem_easy, feedin_rem_easy = run_battery_simulation(df, 'consumption_easy', 'production_kw')

# Hard Mode (XGBoost)
soc_xgb, grid_rem_xgb, feedin_rem_xgb = run_battery_simulation(df, 'consumption_xgb', 'production_kw')

print("   → Battery simulations completed")

# ============================================
# PLOTTING FUNCTION (PDF Style)
# ============================================
def plot_pdf_style(df, date, title, consumption_col, feedin_col, soc_series, grid_rem_series, feedin_rem_series, filename):
    """Create PDF-style battery visualization"""
    
    day = df.loc[date].copy()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), 
                                    gridspec_kw={'height_ratios': [3, 1.5]},
                                    sharex=True)
    
    # Top plot - Power
    ax1.plot(day.index, day['production_kw'], label='PV Production', color='#f39c12', linewidth=2.2)
    ax1.plot(day.index, day[consumption_col], label='Consumption (Reconstructed)', color='#e74c3c', linewidth=2, linestyle='--')
    ax1.plot(day.index, day['consumption_kw'], label='Consumption (Ground Truth)', color='#c0392b', linewidth=1.5, alpha=0.6)
    
    # Grid consumption remaining (blue)
    ax1.fill_between(day.index, 0, grid_rem_series.loc[date], 
                     alpha=0.6, color='#3498db', label='Grid consumption remaining')
    
    # Feed-in remaining (green)
    ax1.fill_between(day.index, 0, feedin_rem_series.loc[date], 
                     alpha=0.6, color='#27ae60', label='Feed-in remaining after battery')
    
    ax1.set_title(title, fontsize=13, fontweight='bold', pad=10)
    ax1.set_ylabel('Power (kW)', fontsize=11)
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax1.set_ylim(0, 160)
    ax1.grid(True, alpha=0.3)
    
    # Bottom plot - SOC
    ax2.fill_between(day.index, 0, soc_series.loc[date], 
                     alpha=0.7, color='#9b59b6', label='Battery SOC')
    ax2.plot(day.index, soc_series.loc[date], color='#8e44ad', linewidth=1.5)
    
    ax2.set_ylabel('Battery SOC (kWh)', fontsize=11)
    ax2.set_xlabel('Time', fontsize=11)
    ax2.set_ylim(0, 110)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right', fontsize=9)
    
    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"   → Saved: {filename}")

# ============================================
# GENERATE PLOTS FOR 3 SCENARIOS
# ============================================
print("\n[3/4] Generating PDF-style visualizations...")

# Choose a good sunny summer day
date = '2023-06-15'

# 1. Ground Truth (reference)
plot_pdf_style(
    df, date,
    'Ground Truth - 100 kWh / 50 kW Battery (Reference)',
    'consumption_kw', 'feed_in_kw',
    soc_gt, grid_rem_gt, feedin_rem_gt,
    'pdf_style_ground_truth.png'
)

# 2. Easy Mode
plot_pdf_style(
    df, date,
    'Easy Mode - 100 kWh / 50 kW Battery (Reconstructed Consumption)',
    'consumption_easy', 'feed_in_kw',
    soc_easy, grid_rem_easy, feedin_rem_easy,
    'pdf_style_easy_mode.png'
)

# 3. Hard Mode (XGBoost)
plot_pdf_style(
    df, date,
    'Hard Mode (XGBoost) - 100 kWh / 50 kW Battery (Reconstructed Consumption + Feed-in)',
    'consumption_xgb', 'feed_in_xgb',
    soc_xgb, grid_rem_xgb, feedin_rem_xgb,
    'pdf_style_hard_mode_xgboost.png'
)

print("\n[4/4] All visualizations completed!")

print("\n" + "=" * 70)
print("PHASE 7: PDF-STYLE VISUALIZATIONS COMPLETED")
print("=" * 70)