# Grid results (auto-generated)
Cells: 24  |  successful: 24

## RQ1 Point accuracy (mean MAE across seeds)
|                            |   MAE_main_mean |   MAE_main_std |   MAE_persistence_mean |   MAE_persistence_std |
|:---------------------------|----------------:|---------------:|-----------------------:|----------------------:|
| ('opsd', 'injected_drift') |         1483.39 |           0    |                4457.62 |                     0 |
| ('opsd', 'missing')        |         1001.03 |          12.52 |                3616.76 |                     0 |
| ('opsd', 'noise')          |         1262.68 |           6.67 |                3616.76 |                     0 |
| ('opsd', 'normal')         |          805.57 |           0    |                3616.76 |                     0 |
| ('uci', 'injected_drift')  |            0.95 |           0    |                   1.07 |                     0 |
| ('uci', 'missing')         |            0.34 |           0    |                   0.54 |                     0 |
| ('uci', 'noise')           |            0.47 |           0    |                   0.54 |                     0 |
| ('uci', 'normal')          |            0.32 |           0    |                   0.54 |                     0 |

## RQ2/RQ3 Adaptation family: drift-region coverage, width, interval score
Static baseline vs windowed / ACI / AgACI competitors. Drift-PICP target 0.90; lower interval score is better.

|                            |   static_drift_PICP_mean |   static_drift_PICP_std |   static_PINAW_mean |   static_PINAW_std |   static_interval_score_mean |   static_interval_score_std |   windowed_drift_PICP_mean |   windowed_drift_PICP_std |   windowed_PINAW_mean |   windowed_PINAW_std |   windowed_interval_score_mean |   windowed_interval_score_std |   adaptive_drift_PICP_mean |   adaptive_drift_PICP_std |   adaptive_PINAW_mean |   adaptive_PINAW_std |   adaptive_interval_score_mean |   adaptive_interval_score_std |   agaci_drift_PICP_mean |   agaci_drift_PICP_std |   agaci_PINAW_mean |   agaci_PINAW_std |   agaci_interval_score_mean |   agaci_interval_score_std |
|:---------------------------|-------------------------:|------------------------:|--------------------:|-------------------:|-----------------------------:|----------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|------------------------:|-----------------------:|-------------------:|------------------:|----------------------------:|---------------------------:|
| ('opsd', 'injected_drift') |                    0.453 |                   0     |               0.061 |                  0 |                    14535.2   |                       0     |                      0.883 |                     0     |                 0.132 |                0     |                       8602.76  |                         0     |                      0.903 |                     0     |                 0.136 |                0     |                       8305.39  |                         0     |                   0.896 |                  0     |              0.132 |             0     |                    8206.32  |                      0     |
| ('opsd', 'missing')        |                    0.771 |                   0.003 |               0.067 |                  0 |                     7373.72  |                     182.253 |                      0.9   |                     0.001 |                 0.097 |                0.001 |                       6671.13  |                       178.416 |                      0.901 |                     0.001 |                 0.098 |                0.001 |                       6645.41  |                       162.764 |                   0.899 |                  0.001 |              0.097 |             0.001 |                    6670.33  |                    168.713 |
| ('opsd', 'noise')          |                    0.662 |                   0.002 |               0.067 |                  0 |                     9586.84  |                     133.891 |                      0.902 |                     0.002 |                 0.12  |                0.002 |                       7383.15  |                       121.466 |                      0.9   |                     0     |                 0.122 |                0.002 |                       7382.95  |                       130.169 |                   0.902 |                  0.001 |              0.12  |             0.002 |                    7375.72  |                    119.943 |
| ('opsd', 'normal')         |                    0.834 |                   0     |               0.067 |                  0 |                     4967.33  |                       0     |                      0.898 |                     0     |                 0.078 |                0     |                       4741.67  |                         0     |                      0.901 |                     0     |                 0.079 |                0     |                       4638.09  |                         0     |                   0.898 |                  0     |              0.079 |             0     |                    4616.11  |                      0     |
| ('uci', 'injected_drift')  |                    0.204 |                   0     |               0.087 |                  0 |                       10.745 |                       0     |                      0.867 |                     0     |                 0.184 |                0     |                          4.675 |                         0     |                      0.9   |                     0     |                 0.191 |                0     |                          4.593 |                         0     |                   0.9   |                  0     |              0.191 |             0     |                       4.589 |                      0     |
| ('uci', 'missing')         |                    0.891 |                   0.005 |               0.28  |                  0 |                        2.354 |                       0.021 |                      0.895 |                     0.002 |                 0.3   |                0.004 |                          2.332 |                         0.012 |                      0.9   |                     0.001 |                 0.303 |                0.004 |                          2.32  |                         0.012 |                   0.9   |                  0.001 |              0.302 |             0.004 |                       2.313 |                      0.01  |
| ('uci', 'noise')           |                    0.8   |                   0.005 |               0.28  |                  0 |                        2.783 |                       0.025 |                      0.899 |                     0.002 |                 0.364 |                0.003 |                          2.581 |                         0.016 |                      0.901 |                     0.001 |                 0.369 |                0.002 |                          2.586 |                         0.011 |                   0.898 |                  0.002 |              0.365 |             0.002 |                       2.58  |                      0.017 |
| ('uci', 'normal')          |                    0.913 |                   0     |               0.28  |                  0 |                        2.18  |                       0     |                      0.896 |                     0     |                 0.278 |                0     |                          2.17  |                         0     |                      0.9   |                     0     |                 0.278 |                0     |                          2.159 |                         0     |                   0.9   |                  0     |              0.277 |             0     |                       2.154 |                      0     |

Paired-bootstrap fraction where each method's drift coverage differs significantly from static:

|                            |   rq3_windowed_significant |   rq3_adaptive_significant |   rq3_agaci_significant |
|:---------------------------|---------------------------:|---------------------------:|------------------------:|
| ('opsd', 'injected_drift') |                          1 |                          1 |                       1 |
| ('opsd', 'missing')        |                          1 |                          1 |                       1 |
| ('opsd', 'noise')          |                          1 |                          1 |                       1 |
| ('opsd', 'normal')         |                          1 |                          1 |                       1 |
| ('uci', 'injected_drift')  |                          1 |                          1 |                       1 |
| ('uci', 'missing')         |                          0 |                          0 |                       0 |
| ('uci', 'noise')           |                          1 |                          1 |                       1 |
| ('uci', 'normal')          |                          1 |                          1 |                       1 |

## Equivalence to nominal (practical calibration)
Fraction of cells whose block-bootstrap drift-coverage CI lies entirely within [0.90±δ] — superiority over static is not the same as being *practically calibrated*.

|                  |   fraction_calibrated |
|:-----------------|----------------------:|
| static_equiv02   |                  0.04 |
| static_equiv05   |                  0.25 |
| windowed_equiv02 |                  0.58 |
| windowed_equiv05 |                  0.88 |
| adaptive_equiv02 |                  1    |
| adaptive_equiv05 |                  1    |
| agaci_equiv02    |                  1    |
| agaci_equiv05    |                  1    |

## RQ4/RQ6 Detection: label-free explanation trigger vs residual trigger
Lead = steps the trigger fires before static coverage visibly breaks (positive = early warning). Explanation signal is label-free.

|                            |   page_hinkley_FAR_mean |   page_hinkley_FAR_std |   page_hinkley_lead_mean |   page_hinkley_lead_std |   explanation_shift_FAR_mean |   explanation_shift_FAR_std |   explanation_shift_lead_mean |   explanation_shift_lead_std |
|:---------------------------|------------------------:|-----------------------:|-------------------------:|------------------------:|-----------------------------:|----------------------------:|------------------------------:|-----------------------------:|
| ('opsd', 'injected_drift') |                   0.992 |                      0 |                        0 |                       0 |                         0.01 |                           0 |                          -102 |                            0 |
| ('opsd', 'missing')        |                 nan     |                    nan |                      nan |                     nan |                       nan    |                         nan |                           nan |                          nan |
| ('opsd', 'noise')          |                 nan     |                    nan |                      nan |                     nan |                       nan    |                         nan |                           nan |                          nan |
| ('opsd', 'normal')         |                 nan     |                    nan |                      nan |                     nan |                       nan    |                         nan |                           nan |                          nan |
| ('uci', 'injected_drift')  |                   0     |                      0 |                      -25 |                       0 |                         0.02 |                           0 |                           -50 |                            0 |
| ('uci', 'missing')         |                 nan     |                    nan |                      nan |                     nan |                       nan    |                         nan |                           nan |                          nan |
| ('uci', 'noise')           |                 nan     |                    nan |                      nan |                     nan |                       nan    |                         nan |                           nan |                          nan |
| ('uci', 'normal')          |                 nan     |                    nan |                      nan |                     nan |                       nan    |                         nan |                           nan |                          nan |

## RQ5 coverage-before-accuracy (steps, >0 = coverage first) & RQ7 fidelity (>1 = faithful)
|                            |   rq5_cov_before_acc_mean |   rq5_cov_before_acc_std |   fidelity_ratio_mean |   fidelity_ratio_std |
|:---------------------------|--------------------------:|-------------------------:|----------------------:|---------------------:|
| ('opsd', 'injected_drift') |                   -600    |                     0    |                  3.71 |                 0.79 |
| ('opsd', 'missing')        |                   -727.33 |                   131.34 |                  3.41 |                 0.63 |
| ('opsd', 'noise')          |                   -568    |                   681.3  |                  3.73 |                 0.77 |
| ('opsd', 'normal')         |                   -600    |                     0    |                  3.45 |                 0.67 |
| ('uci', 'injected_drift')  |                      3    |                     0    |                  2.86 |                 2.23 |
| ('uci', 'missing')         |                     13.33 |                    15.04 |                  2.25 |                 1.42 |
| ('uci', 'noise')           |                  -1746.67 |                  4094.69 |                  4.2  |                 3.84 |
| ('uci', 'normal')          |                      3    |                     0    |                  2.29 |                 1.43 |