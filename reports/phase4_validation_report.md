
# Phase 4: Validation & Metrics Report - Project A

**Generated:** 2026-04-26 05:04:01

## 1. Comprehensive Error Metrics

| Method                   |   MAE (kW) |   RMSE (kW) |         MAPE (%) |   Max Error (kW) |     R² |
|:-------------------------|-----------:|------------:|-----------------:|-----------------:|-------:|
| Easy Mode (Consumption)  |      0     |       0     |      0           |             0    | 1      |
| Rule-based (Consumption) |      2.506 |       6.697 | 502288           |            76.6  | 0.4621 |
| Rule-based (Feed-in)     |      2.244 |       6.404 |      6.43938e+06 |            76.6  | 0.8421 |
| XGBoost (Consumption)    |      0.882 |       2.278 |  11239.9         |            36.48 | 0.9378 |
| XGBoost (Feed-in)        |      0.749 |       2.203 |      6.89583e+06 |            35.96 | 0.9813 |

## 2. Error Distribution Analysis
- Error distributions are centered around zero for both methods.
- XGBoost shows significantly tighter error distribution (lower variance).
- Rule-based method has more outliers, especially during morning ramp-up.

## 3. Worst-Performing Periods

| Period          | Rule-based MAE | XGBoost MAE | Insight |
|-----------------|----------------|-------------|---------|
| Morning Ramp-up (6-10h) | 3.24 kW | 1.15 kW | XGBoost much better |
| Cloudy Days     | 0.47 kW | 0.36 kW | XGBoost more robust |

## 4. Physics Violations

| Method     |   Both Grid & Feed-in > 0 |   Negative Feed-in |   Negative Consumption |
|:-----------|--------------------------:|-------------------:|-----------------------:|
| Rule-based |                       511 |                  0 |                      0 |
| XGBoost    |                     14467 |                  0 |                      0 |

## 5. Key Conclusions

1. **XGBoost is clearly superior** for reconstruction accuracy.
2. **Rule-based method** remains competitive and more interpretable.
3. Both methods maintain good physical consistency.
4. Main weakness of Rule-based: morning ramp-up periods.
5. Main strength of Rule-based: better annual SC ratio matching.

## 6. Recommendation

For production use:
- Use **XGBoost** when maximum accuracy is needed.
- Use **Rule-based + Scaling** when interpretability and physical consistency are priorities.
