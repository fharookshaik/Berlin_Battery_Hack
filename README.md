# Berlin Battery Hackathon - Project A

## Overview

This project analyzes and reconstructs energy consumption data from a residential solar+battery system (Project A) as part of the Green Energy Tools Battery Hackathon. The goal is to reconstruct missing consumption measurements using available production, grid consumption, and feed-in data.

## Project Structure

```
Berlin_Battery_Hack/
├── data/
│   └── raw/
│       └── project_A.xlsx          # Raw input data
├── src/
│   ├── data_loader.py             # Phase 1: Data loading and exploration
│   ├── easy_mode.py               # Simple physical formula reconstruction
│   ├── hard_mode.py               # Advanced modeling (rule-based + XGBoost)
│   ├── battery_sim.py             # Battery simulation tools
│   ├── battery_soc_visualizations.py # State of charge visualizations
│   ├── metrics.py                 # Metrics calculation utilities
│   └── visualization.py           # Visualization helpers
├── outputs/
│   ├── reconstructions/           # Reconstructed consumption data
│   ├── plots/                     # Generated visualizations
│   └── metrics/                   # Performance metrics and reports
├── reports/                       # Written reports and documentation
├── main.py                        # Entry point
├── pyproject.toml                 # Project dependencies
└── README.md                      # This file
```

## Features

### Phase 1: Data Loading & Exploration (`src/data_loader.py`)
- Loads and validates Project A energy data (15-minute resolution, full year 2023)
- Performs data integrity checks (missing values, duplicates, gaps)
- Calculates basic statistics and annual totals
- Verifies physics constraints (no simultaneous grid import/export)
- Analyzes night-time behavior (production = 0)
- Saves processed data as Parquet and generates quality metrics

### Easy Mode (`src/easy_mode.py`)
- Applies physical reconstruction formula: `consumption = production + grid_consumption - feed_in`
- Calculates error metrics (MAE, RMSE, MAPE, R²)
- Validates annual energy balance
- Generates sample day visualizations (summer, winter, spring)
- Saves reconstructed data and metrics

### Hard Mode (`src/hard_mode.py`)
**Method 1: Rule-based + Annual Scaling**
- Uses physical rules for grid import/export periods
- Applies time-of-day median profiles for grid export periods
- Scales surplus to match target self-consumption ratio (37.5%)

**Method 2: XGBoost Model**
- Trains two XGBoost regressors (for feed-in and consumption)
- Features: production, grid consumption, hour, day of week, month
- Evaluates both methods on feed-in MAE, consumption MAE, and self-consumption ratio error
- Generates comparison visualizations

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Berlin_Battery_Hack

# Create virtual environment (if not already present)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Verify installation
python -c "import pandas, numpy, matplotlib, xgboost; print('All packages imported successfully')"
```

## Usage

### Run Individual Components
```bash
# Phase 1: Data loading and exploration
python src/data_loader.py

# Easy mode reconstruction
python src/easy_mode.py

# Hard mode advanced modeling
python src/hard_mode.py
```

## Dependencies

See `pyproject.toml` for complete dependency list:
- pandas>=3.0.2
- numpy>=2.4.4
- matplotlib>=3.10.9
- seaborn>=0.13.2
- scikit-learn>=1.8.0
- xgboost>=3.2.0
- fastparquet>=2026.3.0
- pyarrow>=24.0.0
- openpyxl>=3.1.5
- tabulate>=0.10.0

## Outputs

### Data Outputs
- `data/processed/project_A.parquet` - Cleaned, processed dataset
- `outputs/reconstructions/` - Consumption reconstructions:
  - `easy_mode_reconstruction.csv`
  - `hard_mode_rule_based.csv`
  - `hard_mode_xgboost.csv`

### Metrics
- `outputs/metrics/` - Performance metrics:
  - `phase1_data_quality.json` - Data exploration results
  - `easy_mode_metrics.json` - Easy mode performance
  - `hard_mode_comparison.json` - Hard mode method comparison
  - Additional metric files from various phases

### Visualizations
- `outputs/plots/` - Generated plots:
  - Daily comparisons for sample dates (summer, winter, spring)
  - Error distributions
  - Energy balance visualizations
  - Method comparison plots

## Key Findings

Based on the analysis:

1. **Data Quality**: The dataset contains 35,040 intervals (full year at 15-minute resolution) with minimal gaps and no physically impossible simultaneous grid import/export.

2. **Easy Mode Performance**: 
   - MAE: ~0.035 kW
   - RMSE: ~0.105 kW
   - MAPE: ~3.34%
   - R²: ~0.997
   - Annual balance error: 0.03% (excellent)

3. **Hard Mode Performance**:
   - Both rule-based and XGBoost methods achieve excellent self-consumption ratio matching (target: 37.5%)
   - Rule-based method shows slightly better performance on consumption reconstruction
   - XGBoost captures more complex patterns but may overfit to noise

## Future Improvements

1. Incorporate weather data (solar irradiance, temperature) for better production prediction
2. Add battery state-of-charge constraints to the reconstruction
3. Experiment with different ML algorithms (LSTM, Prophet) for time-series forecasting
4. Implement uncertainty quantification in reconstructions
5. Expand to multiple projects/houses for generalization testing

## License

This project was created for the Berlin Battery Hackathon. Please refer to the hackathon guidelines for usage restrictions.

## Acknowledgments

Thanks to the Green Energy Tools organizers and participants for the hackathon opportunity and data provision.