# Grid results (auto-generated)
Cells: 16  |  successful: 16

## RQ1 Point accuracy (mean MAE across seeds)
|              |   MAE_main_mean |   MAE_main_std |   MAE_persistence_mean |   MAE_persistence_std |
|:-------------|----------------:|---------------:|-----------------------:|----------------------:|
| ('opsd', 1)  |         1260.39 |         273.78 |                4258.05 |                219.98 |
| ('opsd', 24) |         1938.32 |         324.84 |                5399.78 |                166.09 |
| ('uci', 1)   |            0.99 |           0.04 |                   1.22 |                  0.16 |
| ('uci', 24)  |            1.16 |           0.1  |                   1.3  |                  0.2  |

## RQ2/RQ3 Adaptation family: drift-region coverage, width, interval score
Static baseline vs windowed / ACI / AgACI competitors. Drift-PICP target 0.90; lower interval score is better.

|              |   static_drift_PICP_mean |   static_drift_PICP_std |   static_PINAW_mean |   static_PINAW_std |   static_interval_score_mean |   static_interval_score_std |   windowed_drift_PICP_mean |   windowed_drift_PICP_std |   windowed_PINAW_mean |   windowed_PINAW_std |   windowed_interval_score_mean |   windowed_interval_score_std |   adaptive_drift_PICP_mean |   adaptive_drift_PICP_std |   adaptive_PINAW_mean |   adaptive_PINAW_std |   adaptive_interval_score_mean |   adaptive_interval_score_std |   agaci_drift_PICP_mean |   agaci_drift_PICP_std |   agaci_PINAW_mean |   agaci_PINAW_std |   agaci_interval_score_mean |   agaci_interval_score_std |
|:-------------|-------------------------:|------------------------:|--------------------:|-------------------:|-----------------------------:|----------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|------------------------:|-----------------------:|-------------------:|------------------:|----------------------------:|---------------------------:|
| ('opsd', 1)  |                    0.59  |                   0.146 |               0.066 |              0.007 |                    10995.6   |                    4105.8   |                      0.881 |                     0.012 |                 0.115 |                0.021 |                       7488.9   |                      1559.69  |                      0.9   |                     0.002 |                 0.119 |                0.024 |                       7211.77  |                      1510.15  |                   0.895 |                  0.005 |              0.114 |             0.019 |                    6971.6   |                   1335.64  |
| ('opsd', 24) |                    0.76  |                   0.102 |               0.135 |              0.011 |                    14806.3   |                    3205.4   |                      0.884 |                     0.015 |                 0.175 |                0.022 |                      13482.9   |                      1982.81  |                      0.889 |                     0.002 |                 0.198 |                0.022 |                      14056.2   |                      1727.18  |                   0.885 |                  0.006 |              0.188 |             0.028 |                   13827.6   |                   1624.44  |
| ('uci', 1)   |                    0.231 |                   0.028 |               0.102 |              0.018 |                       11.266 |                       0.907 |                      0.867 |                     0.013 |                 0.217 |                0.023 |                          5.366 |                         0.753 |                      0.9   |                     0.002 |                 0.232 |                0.028 |                          5.231 |                         0.693 |                   0.893 |                  0.013 |              0.227 |             0.026 |                       5.271 |                      0.734 |
| ('uci', 24)  |                    0.27  |                   0.033 |               0.14  |              0.03  |                       11.276 |                       1.466 |                      0.868 |                     0.012 |                 0.259 |                0.036 |                          6.362 |                         1.052 |                      0.899 |                     0.002 |                 0.287 |                0.04  |                          6.457 |                         1.023 |                   0.893 |                  0.011 |              0.272 |             0.039 |                       6.331 |                      1.089 |

Paired-bootstrap fraction where each method's drift coverage differs significantly from static:

|              |   rq3_windowed_significant |   rq3_adaptive_significant |   rq3_agaci_significant |
|:-------------|---------------------------:|---------------------------:|------------------------:|
| ('opsd', 1)  |                       1    |                       1    |                    1    |
| ('opsd', 24) |                       0.75 |                       0.75 |                    0.75 |
| ('uci', 1)   |                       1    |                       1    |                    1    |
| ('uci', 24)  |                       1    |                       1    |                    1    |

## Equivalence to nominal (practical calibration)
Fraction of cells whose block-bootstrap drift-coverage CI lies entirely within [0.90±δ] — superiority over static is not the same as being *practically calibrated*.

|                  |   fraction_calibrated |
|:-----------------|----------------------:|
| static_equiv02   |                  0    |
| static_equiv05   |                  0.06 |
| windowed_equiv02 |                  0    |
| windowed_equiv05 |                  0.5  |
| adaptive_equiv02 |                  0.62 |
| adaptive_equiv05 |                  1    |
| agaci_equiv02    |                  0.38 |
| agaci_equiv05    |                  1    |

## RQ4/RQ6 Detection: label-free explanation trigger vs residual trigger
Lead = steps the trigger fires before static coverage visibly breaks (positive = early warning). Explanation signal is label-free.

|              |   page_hinkley_FAR_mean |   page_hinkley_FAR_std |   page_hinkley_lead_mean |   page_hinkley_lead_std |   explanation_shift_FAR_mean |   explanation_shift_FAR_std |   explanation_shift_lead_mean |   explanation_shift_lead_std |
|:-------------|------------------------:|-----------------------:|-------------------------:|------------------------:|-----------------------------:|----------------------------:|------------------------------:|-----------------------------:|
| ('opsd', 1)  |                   0.929 |                  0.056 |                    32.75 |                  37.071 |                        0.008 |                       0.002 |                        -29    |                       52.466 |
| ('opsd', 24) |                   0.875 |                  0.159 |                   165.75 |                 184.809 |                        0.009 |                       0.001 |                         92.25 |                      189.144 |
| ('uci', 1)   |                   0.011 |                  0.022 |                   -17.75 |                  12.312 |                        0.018 |                       0.002 |                        -29    |                       34.303 |
| ('uci', 24)  |                   0.142 |                  0.283 |                   -24.5  |                  17.916 |                        0.012 |                       0.003 |                       -126.5  |                      218.028 |

## RQ5 coverage-before-accuracy (steps, >0 = coverage first) & RQ7 fidelity (>1 = faithful)
|              |   rq5_cov_before_acc_mean |   rq5_cov_before_acc_std |   fidelity_ratio_mean |   fidelity_ratio_std |
|:-------------|--------------------------:|-------------------------:|----------------------:|---------------------:|
| ('opsd', 1)  |                   -150.25 |                   299.91 |                  3.71 |                 0.19 |
| ('opsd', 24) |                     25.25 |                    42.04 |                  2.25 |                 0.55 |
| ('uci', 1)   |                   -331.75 |                   673.52 |                  5.4  |                 0.86 |
| ('uci', 24)  |                   -283.5  |                   703.97 |                  2.75 |                 1.72 |