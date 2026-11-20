# Grid results (auto-generated)
Cells: 16  |  successful: 16

## RQ1 Point accuracy (mean MAE across seeds)
|              |   MAE_main_mean |   MAE_main_std |   MAE_persistence_mean |   MAE_persistence_std |
|:-------------|----------------:|---------------:|-----------------------:|----------------------:|
| ('opsd', 1)  |         1459.02 |          88.23 |                4413.7  |                119.23 |
| ('opsd', 24) |         2048.16 |          39.83 |                5156.93 |                 29.14 |
| ('uci', 1)   |            0.94 |           0.14 |                   1.09 |                  0.11 |
| ('uci', 24)  |            1.05 |           0.13 |                   1.14 |                  0.11 |

## RQ2/RQ3 Adaptation family: drift-region coverage, width, interval score
Static baseline vs windowed / ACI / AgACI competitors. Drift-PICP target 0.90; lower interval score is better.

|              |   static_drift_PICP_mean |   static_drift_PICP_std |   static_PINAW_mean |   static_PINAW_std |   static_interval_score_mean |   static_interval_score_std |   windowed_drift_PICP_mean |   windowed_drift_PICP_std |   windowed_PINAW_mean |   windowed_PINAW_std |   windowed_interval_score_mean |   windowed_interval_score_std |   adaptive_drift_PICP_mean |   adaptive_drift_PICP_std |   adaptive_PINAW_mean |   adaptive_PINAW_std |   adaptive_interval_score_mean |   adaptive_interval_score_std |   agaci_drift_PICP_mean |   agaci_drift_PICP_std |   agaci_PINAW_mean |   agaci_PINAW_std |   agaci_interval_score_mean |   agaci_interval_score_std |
|:-------------|-------------------------:|------------------------:|--------------------:|-------------------:|-----------------------------:|----------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|------------------------:|-----------------------:|-------------------:|------------------:|----------------------------:|---------------------------:|
| ('opsd', 1)  |                    0.468 |                   0.029 |               0.061 |                  0 |                    14029     |                    1216.52  |                      0.885 |                     0.005 |                 0.13  |                0.009 |                       8477.62  |                       484.403 |                      0.9   |                     0.002 |                 0.134 |                0.009 |                       8199.88  |                       503.954 |                   0.895 |                  0.003 |              0.128 |             0.007 |                    8086.87  |                    497.593 |
| ('opsd', 24) |                    0.698 |                   0.012 |               0.124 |                  0 |                    14605.8   |                     322.973 |                      0.901 |                     0.012 |                 0.171 |                0.004 |                      12717.7   |                       289.35  |                      0.891 |                     0.004 |                 0.187 |                0.007 |                      13131.6   |                       469.358 |                   0.88  |                  0.005 |              0.184 |             0.005 |                   13447.9   |                    439.667 |
| ('uci', 1)   |                    0.216 |                   0.004 |               0.087 |                  0 |                       10.653 |                       1.897 |                      0.863 |                     0.013 |                 0.184 |                0.019 |                          4.703 |                         0.41  |                      0.899 |                     0.003 |                 0.191 |                0.02  |                          4.618 |                         0.39  |                   0.899 |                  0.003 |              0.191 |             0.02  |                       4.614 |                      0.39  |
| ('uci', 24)  |                    0.278 |                   0.008 |               0.113 |                  0 |                       10.28  |                       1.524 |                      0.866 |                     0.013 |                 0.21  |                0.02  |                          5.37  |                         0.406 |                      0.899 |                     0.002 |                 0.227 |                0.024 |                          5.505 |                         0.449 |                   0.896 |                  0.001 |              0.219 |             0.017 |                       5.353 |                      0.394 |

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
| windowed_equiv02 |                  0    |
| windowed_equiv05 |                  0.75 |
| adaptive_equiv02 |                  0.62 |
| adaptive_equiv05 |                  1    |
| agaci_equiv02    |                  0.62 |
| agaci_equiv05    |                  1    |

## RQ4/RQ6 Detection: label-free explanation trigger vs residual trigger
Lead = steps the trigger fires before static coverage visibly breaks (positive = early warning). Explanation signal is label-free.

|              |   page_hinkley_FAR_mean |   page_hinkley_FAR_std |   page_hinkley_lead_mean |   page_hinkley_lead_std |   explanation_shift_FAR_mean |   explanation_shift_FAR_std |   explanation_shift_lead_mean |   explanation_shift_lead_std |
|:-------------|------------------------:|-----------------------:|-------------------------:|------------------------:|-----------------------------:|----------------------------:|------------------------------:|-----------------------------:|
| ('opsd', 1)  |                   0.991 |                  0.002 |                     79.5 |                  91.799 |                        0.01  |                       0.001 |                          26   |                       35.796 |
| ('opsd', 24) |                   0.96  |                  0.009 |                    209   |                 241.332 |                        0.007 |                       0     |                        -202   |                      632.776 |
| ('uci', 1)   |                   0     |                  0     |                    -23   |                   9.238 |                        0.021 |                       0.001 |                          -5   |                       31.177 |
| ('uci', 24)  |                   0     |                  0     |                    -38.5 |                   0.577 |                        0.015 |                       0     |                          -3.5 |                        5.196 |

## RQ5 coverage-before-accuracy (steps, >0 = coverage first) & RQ7 fidelity (>1 = faithful)
|              |   rq5_cov_before_acc_mean |   rq5_cov_before_acc_std |   fidelity_ratio_mean |   fidelity_ratio_std |
|:-------------|--------------------------:|-------------------------:|----------------------:|---------------------:|
| ('opsd', 1)  |                    -309   |                   346.41 |                  4.11 |                 0.38 |
| ('opsd', 24) |                       4   |                     1.15 |                  2.43 |                 0.6  |
| ('uci', 1)   |                      36   |                     2.31 |                  3.7  |                 2    |
| ('uci', 24)  |                      52.5 |                    54.85 |                  1.38 |                 0.36 |