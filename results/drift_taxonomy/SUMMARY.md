# Grid results (auto-generated)
Cells: 60  |  successful: 60

## RQ1 Point accuracy (mean MAE across seeds)
| dataset   |   MAE_main_mean |   MAE_main_std |   MAE_persistence_mean |   MAE_persistence_std |
|:----------|----------------:|---------------:|-----------------------:|----------------------:|
| opsd      |         1611.49 |        1492.49 |                4276.38 |               1139.27 |

## RQ2/RQ3 Adaptation family: drift-region coverage, width, interval score
Static baseline vs windowed / ACI / AgACI competitors. Drift-PICP target 0.90; lower interval score is better.

| dataset   |   static_drift_PICP_mean |   static_drift_PICP_std |   static_PINAW_mean |   static_PINAW_std |   static_interval_score_mean |   static_interval_score_std |   windowed_drift_PICP_mean |   windowed_drift_PICP_std |   windowed_PINAW_mean |   windowed_PINAW_std |   windowed_interval_score_mean |   windowed_interval_score_std |   adaptive_drift_PICP_mean |   adaptive_drift_PICP_std |   adaptive_PINAW_mean |   adaptive_PINAW_std |   adaptive_interval_score_mean |   adaptive_interval_score_std |   agaci_drift_PICP_mean |   agaci_drift_PICP_std |   agaci_PINAW_mean |   agaci_PINAW_std |   agaci_interval_score_mean |   agaci_interval_score_std |
|:----------|-------------------------:|------------------------:|--------------------:|-------------------:|-----------------------------:|----------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|------------------------:|-----------------------:|-------------------:|------------------:|----------------------------:|---------------------------:|
| opsd      |                    0.654 |                   0.232 |               0.061 |              0.012 |                      18665.5 |                     27644.2 |                      0.888 |                     0.011 |                 0.117 |                0.059 |                        9408.68 |                       8988.81 |                      0.898 |                     0.001 |                 0.121 |                0.063 |                        9073.17 |                       8487.87 |                   0.895 |                  0.004 |              0.113 |              0.05 |                     8383.25 |                    6857.15 |

Paired-bootstrap fraction where each method's drift coverage differs significantly from static:

| dataset   |   rq3_windowed_significant |   rq3_adaptive_significant |   rq3_agaci_significant |
|:----------|---------------------------:|---------------------------:|------------------------:|
| opsd      |                          1 |                          1 |                       1 |

## Equivalence to nominal (practical calibration)
Fraction of cells whose block-bootstrap drift-coverage CI lies entirely within [0.90±δ] — superiority over static is not the same as being *practically calibrated*.

|                  |   fraction_calibrated |
|:-----------------|----------------------:|
| static_equiv02   |                  0    |
| static_equiv05   |                  0    |
| windowed_equiv02 |                  0.53 |
| windowed_equiv05 |                  0.93 |
| adaptive_equiv02 |                  1    |
| adaptive_equiv05 |                  1    |
| agaci_equiv02    |                  0.97 |
| agaci_equiv05    |                  1    |

## RQ4/RQ6 Detection: label-free explanation trigger vs residual trigger
Lead = steps the trigger fires before static coverage visibly breaks (positive = early warning). Explanation signal is label-free.

| dataset   |   page_hinkley_FAR_mean |   page_hinkley_FAR_std |   page_hinkley_lead_mean |   page_hinkley_lead_std |   explanation_shift_FAR_mean |   explanation_shift_FAR_std |   explanation_shift_lead_mean |   explanation_shift_lead_std |
|:----------|------------------------:|-----------------------:|-------------------------:|------------------------:|-----------------------------:|----------------------------:|------------------------------:|-----------------------------:|
| opsd      |                    0.99 |                      0 |                    402.8 |                 325.204 |                        0.011 |                           0 |                       303.867 |                      321.967 |

## RQ5 coverage-before-accuracy (steps, >0 = coverage first) & RQ7 fidelity (>1 = faithful)
| dataset   |   rq5_cov_before_acc_mean |   rq5_cov_before_acc_std |   fidelity_ratio_mean |   fidelity_ratio_std |
|:----------|--------------------------:|-------------------------:|----------------------:|---------------------:|
| opsd      |                      -609 |                        0 |                  4.09 |                 0.57 |