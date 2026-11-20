# Grid results (auto-generated)
Cells: 8  |  successful: 8

## RQ1 Point accuracy (mean MAE across seeds)
|              |   MAE_main_mean |   MAE_main_std |   MAE_persistence_mean |   MAE_persistence_std |
|:-------------|----------------:|---------------:|-----------------------:|----------------------:|
| ('opsd', 1)  |          635.39 |          18.83 |                4413.7  |                146.03 |
| ('opsd', 24) |         2644.76 |          52.65 |                5156.93 |                 35.69 |
| ('uci', 1)   |            0.88 |           0.14 |                   1.09 |                  0.13 |
| ('uci', 24)  |            1.04 |           0.14 |                   1.14 |                  0.13 |

## RQ2/RQ3 Adaptation family: drift-region coverage, width, interval score
Static baseline vs windowed / ACI / AgACI competitors. Drift-PICP target 0.90; lower interval score is better.

|              |   static_drift_PICP_mean |   static_drift_PICP_std |   static_PINAW_mean |   static_PINAW_std |   static_interval_score_mean |   static_interval_score_std |   windowed_drift_PICP_mean |   windowed_drift_PICP_std |   windowed_PINAW_mean |   windowed_PINAW_std |   windowed_interval_score_mean |   windowed_interval_score_std |   adaptive_drift_PICP_mean |   adaptive_drift_PICP_std |   adaptive_PINAW_mean |   adaptive_PINAW_std |   adaptive_interval_score_mean |   adaptive_interval_score_std |   agaci_drift_PICP_mean |   agaci_drift_PICP_std |   agaci_PINAW_mean |   agaci_PINAW_std |   agaci_interval_score_mean |   agaci_interval_score_std |
|:-------------|-------------------------:|------------------------:|--------------------:|-------------------:|-----------------------------:|----------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|------------------------:|-----------------------:|-------------------:|------------------:|----------------------------:|---------------------------:|
| ('opsd', 1)  |                    0.708 |                   0.013 |               0.04  |                  0 |                     3928.03  |                     168.868 |                      0.894 |                     0     |                 0.054 |                0.002 |                       3436.77  |                        84.92  |                      0.902 |                     0     |                 0.055 |                0.002 |                       3420.07  |                        96.649 |                   0.894 |                  0.001 |              0.054 |             0.002 |                    3426.97  |                     91.877 |
| ('opsd', 24) |                    0.555 |                   0.055 |               0.114 |                  0 |                    25947.4   |                     653.529 |                      0.894 |                     0.011 |                 0.224 |                0.005 |                      18985     |                       238.716 |                      0.895 |                     0.004 |                 0.266 |                0.007 |                      20083.9   |                       564.116 |                   0.894 |                  0.008 |              0.261 |             0.003 |                   19729.8   |                    266.903 |
| ('uci', 1)   |                    0.309 |                   0.003 |               0.103 |                  0 |                        8.587 |                       1.523 |                      0.864 |                     0.023 |                 0.187 |                0.021 |                          4.948 |                         0.51  |                      0.9   |                     0.003 |                 0.198 |                0.024 |                          4.895 |                         0.514 |                   0.897 |                  0.001 |              0.196 |             0.022 |                       4.891 |                      0.5   |
| ('uci', 24)  |                    0.361 |                   0.006 |               0.135 |                  0 |                        8.803 |                       1.165 |                      0.86  |                     0.032 |                 0.222 |                0.021 |                          5.878 |                         0.535 |                      0.898 |                     0.003 |                 0.246 |                0.021 |                          6.118 |                         0.502 |                   0.888 |                  0.005 |              0.228 |             0.019 |                       5.911 |                      0.518 |

Paired-bootstrap fraction where each method's drift coverage differs significantly from static:

|              |   rq3_windowed_significant |   rq3_adaptive_significant |   rq3_agaci_significant |
|:-------------|---------------------------:|---------------------------:|------------------------:|
| ('opsd', 1)  |                          1 |                          1 |                       1 |
| ('opsd', 24) |                          1 |                          1 |                       1 |
| ('uci', 1)   |                          1 |                          1 |                       1 |
| ('uci', 24)  |                          1 |                          1 |                       1 |

## Equivalence to nominal (practical calibration)
Fraction of cells whose block-bootstrap drift-coverage CI lies entirely within [0.90±δ] — superiority over static is not the same as being *practically calibrated*.

|                  |   fraction_calibrated |
|:-----------------|----------------------:|
| static_equiv02   |                  0    |
| static_equiv05   |                  0    |
| windowed_equiv02 |                  0.12 |
| windowed_equiv05 |                  0.75 |
| adaptive_equiv02 |                  0.62 |
| adaptive_equiv05 |                  1    |
| agaci_equiv02    |                  0.5  |
| agaci_equiv05    |                  1    |

## RQ4/RQ6 Detection: label-free explanation trigger vs residual trigger
Lead = steps the trigger fires before static coverage visibly breaks (positive = early warning). Explanation signal is label-free.

|              |   page_hinkley_FAR_mean |   page_hinkley_FAR_std |   page_hinkley_lead_mean |   page_hinkley_lead_std |   explanation_shift_FAR_mean |   explanation_shift_FAR_std |   explanation_shift_lead_mean |   explanation_shift_lead_std |
|:-------------|------------------------:|-----------------------:|-------------------------:|------------------------:|-----------------------------:|----------------------------:|------------------------------:|-----------------------------:|
| ('opsd', 1)  |                   0.977 |                  0.006 |                     26.5 |                  37.477 |                        0.011 |                       0.001 |                         -27   |                       31.113 |
| ('opsd', 24) |                   0.949 |                  0.014 |                    225   |                 318.198 |                        0.013 |                       0.001 |                         171   |                      250.316 |
| ('uci', 1)   |                   0     |                  0     |                    -21   |                   4.243 |                        0.022 |                       0     |                          11.5 |                       17.678 |
| ('uci', 24)  |                   0     |                  0     |                    -44   |                  15.556 |                        0.026 |                       0.001 |                        -117   |                      165.463 |

## RQ5 coverage-before-accuracy (steps, >0 = coverage first) & RQ7 fidelity (>1 = faithful)
|              |   rq5_cov_before_acc_mean |   rq5_cov_before_acc_std |   fidelity_ratio_mean |   fidelity_ratio_std |
|:-------------|--------------------------:|-------------------------:|----------------------:|---------------------:|
| ('opsd', 1)  |                     932.5 |                     4.95 |                  3.28 |                 0.01 |
| ('opsd', 24) |                     -62   |                     1.41 |                  3.89 |                 0.17 |
| ('uci', 1)   |                     -29.5 |                    36.06 |                  4.84 |                 0.25 |
| ('uci', 24)  |                    -171   |                   305.47 |                  7.08 |                 1.66 |