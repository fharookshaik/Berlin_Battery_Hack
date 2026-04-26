import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
RAW_PATH = Path("/Users/fharook/Downloads/hackathon_deliverable/data/raw/project_A.xlsx")
OUTPUTS_DIR = Path("/Users/fharook/Downloads/hackathon_deliverable/outputs")
RECON_DIR = OUTPUTS_DIR / "reconstructions"
PLOTS_DIR = OUTPUTS_DIR / "plots"
METRICS_DIR = OUTPUTS_DIR / "metrics"

RECON_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("HARD MODE - FULL IMPLEMENTATION (Rule-based + XGBoost)")
print("=" * 70)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================
# LOAD DATA
# ============================================
print("[1/8] Loading data...")
df = pd.read_excel(RAW_PATH, sheet_name="data")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp').sort_index()
print(f"   → Loaded {len(df):,} rows")

# ============================================
# METHOD 1: RULE-BASED + ANNUAL SCALING (BASELINE)
# ============================================
print("\n[2/8] Implementing Rule-based + Annual Scaling Baseline...")

df_rule = df.copy()

# Step 1: Rule for grid > 0 intervals
threshold = 0.5
grid_positive = df_rule['grid_consumption_kw'] > threshold

df_rule.loc[grid_positive, 'feed_in_rule'] = 0
df_rule.loc[grid_positive, 'consumption_rule'] = (
    df_rule.loc[grid_positive, 'grid_consumption_kw'] + 
    df_rule.loc[grid_positive, 'production_kw']
)

# Step 2: For grid ≈ 0 intervals - use time-of-day median profile
df_rule['hour'] = df_rule.index.hour
hourly_median = df_rule[df_rule['production_kw'] == 0].groupby('hour')['consumption_kw'].median()

df_rule['baseline_consumption'] = df_rule['hour'].map(hourly_median)

# Initial estimate for grid=0 periods
grid_zero = df_rule['grid_consumption_kw'] <= threshold
df_rule.loc[grid_zero, 'consumption_rule'] = df_rule.loc[grid_zero, 'baseline_consumption']
df_rule.loc[grid_zero, 'feed_in_rule'] = (
    df_rule.loc[grid_zero, 'production_kw'] - df_rule.loc[grid_zero, 'consumption_rule']
).clip(lower=0)

# Step 3: Calculate current self-consumption ratio
total_production = df_rule['production_kw'].sum() / 4 / 1000  # MWh
self_consumed_rule = (df_rule['production_kw'] - df_rule['feed_in_rule']).sum() / 4 / 1000
current_sc_ratio = (self_consumed_rule / total_production) * 100

print(f"   → Initial SC Ratio (before scaling): {current_sc_ratio:.2f}%")
print(f"   → Target SC Ratio: 37.5%")

# Step 4: Scale surplus in grid=0 periods to hit exactly 37.5%
target_sc_ratio = 37.5
scaling_factor = (target_sc_ratio / current_sc_ratio) if current_sc_ratio > 0 else 1.0

# Adjust consumption and feed_in in surplus periods
df_rule.loc[grid_zero, 'consumption_rule'] = df_rule.loc[grid_zero, 'consumption_rule'] * scaling_factor
df_rule.loc[grid_zero, 'feed_in_rule'] = (
    df_rule.loc[grid_zero, 'production_kw'] - df_rule.loc[grid_zero, 'consumption_rule']
).clip(lower=0)

# Recalculate final SC ratio
self_consumed_final = (df_rule['production_kw'] - df_rule['feed_in_rule']).sum() / 4 / 1000
final_sc_ratio = (self_consumed_final / total_production) * 100

print(f"   → Final SC Ratio (after scaling): {final_sc_ratio:.2f}%")

# ============================================
# METHOD 2: XGBOOST MODEL
# ============================================
print("\n[3/8] Training XGBoost Model...")

df_ml = df.copy()
df_ml['hour'] = df_ml.index.hour
df_ml['dayofweek'] = df_ml.index.dayofweek
df_ml['month'] = df_ml.index.month

# Features
features = ['production_kw', 'grid_consumption_kw', 'hour', 'dayofweek', 'month']
X = df_ml[features]
y_feedin = df_ml['feed_in_kw']
y_consumption = df_ml['consumption_kw']

# Train-test split (80-20)
X_train, X_test, yf_train, yf_test, yc_train, yc_test = train_test_split(
    X, y_feedin, y_consumption, test_size=0.2, random_state=42, shuffle=False
)

# Train two XGBoost models
model_feedin = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

model_consumption = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

model_feedin.fit(X_train, yf_train)
model_consumption.fit(X_train, yc_train)

print("   → XGBoost models trained")

# Predict on full dataset
df_ml['feed_in_xgb'] = model_feedin.predict(X)
df_ml['consumption_xgb'] = model_consumption.predict(X)

# Clip negative values
df_ml['feed_in_xgb'] = df_ml['feed_in_xgb'].clip(lower=0)
df_ml['consumption_xgb'] = df_ml['consumption_xgb'].clip(lower=0)

# ============================================
# EVALUATION
# ============================================
print("\n[4/8] Evaluating all methods...")

def evaluate_method(name, pred_feedin, pred_consumption, df):
    mae_f = mean_absolute_error(df['feed_in_kw'], pred_feedin)
    rmse_f = np.sqrt(mean_squared_error(df['feed_in_kw'], pred_feedin))
    mae_c = mean_absolute_error(df['consumption_kw'], pred_consumption)
    rmse_c = np.sqrt(mean_squared_error(df['consumption_kw'], pred_consumption))
    
    # Self-consumption ratio error
    total_prod = df['production_kw'].sum() / 4 / 1000
    sc_pred = (df['production_kw'] - pred_feedin).sum() / 4 / 1000
    sc_ratio_pred = (sc_pred / total_prod) * 100
    sc_error = abs(sc_ratio_pred - 37.5)
    
    return {
        "method": name,
        "feedin_mae": round(mae_f, 3),
        "feedin_rmse": round(rmse_f, 3),
        "consumption_mae": round(mae_c, 3),
        "consumption_rmse": round(rmse_c, 3),
        "sc_ratio_error": round(sc_error, 2)
    }

# Evaluate Rule-based
rule_metrics = evaluate_method(
    "Rule-based + Scaling",
    df_rule['feed_in_rule'],
    df_rule['consumption_rule'],
    df
)

# Evaluate XGBoost
xgb_metrics = evaluate_method(
    "XGBoost",
    df_ml['feed_in_xgb'],
    df_ml['consumption_xgb'],
    df
)

print("\n--- COMPARISON RESULTS ---")
print(f"{'Method':<25} {'Feed-in MAE':>12} {'Cons. MAE':>12} {'SC Error':>10}")
print("-" * 60)
print(f"{'Rule-based + Scaling':<25} {rule_metrics['feedin_mae']:>12.3f} {rule_metrics['consumption_mae']:>12.3f} {rule_metrics['sc_ratio_error']:>10.2f}")
print(f"{'XGBoost':<25} {xgb_metrics['feedin_mae']:>12.3f} {xgb_metrics['consumption_mae']:>12.3f} {xgb_metrics['sc_ratio_error']:>10.2f}")

# ============================================
# SAVE OUTPUTS
# ============================================
print("\n[5/8] Saving outputs...")

# Save Rule-based results
df_rule[['production_kw', 'consumption_kw', 'consumption_rule', 
         'feed_in_kw', 'feed_in_rule', 'grid_consumption_kw']].to_csv(
    RECON_DIR / "hard_mode_rule_based.csv", index=True
)

# Save XGBoost results
df_ml[['production_kw', 'consumption_kw', 'consumption_xgb',
       'feed_in_kw', 'feed_in_xgb', 'grid_consumption_kw']].to_csv(
    RECON_DIR / "hard_mode_xgboost.csv", index=True
)

# Save comparison metrics
comparison = {
    "rule_based": rule_metrics,
    "xgboost": xgb_metrics,
    "timestamp": str(datetime.now())
}

with open(METRICS_DIR / "hard_mode_comparison.json", "w") as f:
    json.dump(comparison, f, indent=2)

print("   → Saved comparison metrics and reconstructed files")

# ============================================
# VISUALIZATIONS
# ============================================
print("\n[6/8] Generating comparison visualizations...")

sns.set_style("whitegrid")
sample_dates = ['2023-06-15', '2023-01-15', '2023-03-22']

for date in sample_dates:
    day = df.loc[date]
    rule_day = df_rule.loc[date]
    xgb_day = df_ml.loc[date]
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # Feed-in Comparison
    axes[0].plot(day.index, day['feed_in_kw'], label='Ground Truth', color='black', linewidth=2)
    axes[0].plot(day.index, rule_day['feed_in_rule'], label='Rule-based', color='#e74c3c', linewidth=1.5, linestyle='--')
    axes[0].plot(day.index, xgb_day['feed_in_xgb'], label='XGBoost', color='#3498db', linewidth=1.5, linestyle=':')
    axes[0].set_title(f'Hard Mode Comparison - Feed-in ({date})', fontsize=13, fontweight='bold')
    axes[0].legend()
    axes[0].set_ylabel('Feed-in (kW)')
    
    # Consumption Comparison
    axes[1].plot(day.index, day['consumption_kw'], label='Ground Truth', color='black', linewidth=2)
    axes[1].plot(day.index, rule_day['consumption_rule'], label='Rule-based', color='#e74c3c', linewidth=1.5, linestyle='--')
    axes[1].plot(day.index, xgb_day['consumption_xgb'], label='XGBoost', color='#3498db', linewidth=1.5, linestyle=':')
    axes[1].set_title(f'Consumption ({date})', fontsize=13, fontweight='bold')
    axes[1].legend()
    axes[1].set_ylabel('Consumption (kW)')
    
    # Error comparison
    axes[2].plot(day.index, rule_day['consumption_rule'] - day['consumption_kw'], 
                 label='Rule-based Error', color='#e74c3c', alpha=0.7)
    axes[2].plot(day.index, xgb_day['consumption_xgb'] - day['consumption_kw'], 
                 label='XGBoost Error', color='#3498db', alpha=0.7)
    axes[2].axhline(0, color='black', linestyle='--', linewidth=1)
    axes[2].set_title('Reconstruction Error', fontsize=13, fontweight='bold')
    axes[2].legend()
    axes[2].set_ylabel('Error (kW)')
    axes[2].set_xlabel('Time')
    
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f"hard_mode_comparison_{date}.png", dpi=150, bbox_inches='tight')
    plt.close()

print("   → Saved 3 comparison plots")

# ============================================
# FINAL SUMMARY
# ============================================
print("\n[7/8] Final Summary...")

print("\n" + "=" * 70)
print("HARD MODE RESULTS - PROJECT A")
print("=" * 70)
print(f"\n{'Method':<25} {'Feed-in MAE':>12} {'Cons. MAE':>12} {'SC Error %':>12}")
print("-" * 65)
print(f"{'Rule-based + Scaling':<25} {rule_metrics['feedin_mae']:>12.3f} {rule_metrics['consumption_mae']:>12.3f} {rule_metrics['sc_ratio_error']:>12.2f}")
print(f"{'XGBoost':<25} {xgb_metrics['feedin_mae']:>12.3f} {xgb_metrics['consumption_mae']:>12.3f} {xgb_metrics['sc_ratio_error']:>12.2f}")

print("\n" + "=" * 70)
print("HARD MODE COMPLETED SUCCESSFULLY")
print("=" * 70)