# Grid results (auto-generated)
Cells: 48  |  successful: 48

## RQ1 Point accuracy (mean MAE across seeds)
|                           |   MAE_main_mean |   MAE_main_std |   MAE_persistence_mean |   MAE_persistence_std |
|:--------------------------|----------------:|---------------:|-----------------------:|----------------------:|
| ('opsd', 'gbm', 1)        |         1459.02 |          88.23 |                4413.7  |                119.23 |
| ('opsd', 'gbm', 24)       |         2048.16 |          39.83 |                5156.93 |                 29.14 |
| ('opsd', 'ridge', 1)      |         2478.07 |          40.79 |                4413.7  |                119.23 |
| ('opsd', 'ridge', 24)     |         4236.48 |          13.77 |                5156.93 |                 29.14 |
| ('uci', 'gbm', 1)         |            0.94 |           0.14 |                   1.09 |                  0.11 |
| ('uci', 'gbm', 24)        |            1.05 |           0.13 |                   1.14 |                  0.11 |
| ('uci', 'ridge', 1)       |            0.99 |           0.13 |                   1.09 |                  0.11 |
| ('uci', 'ridge', 24)      |            1.01 |           0.11 |                   1.14 |                  0.11 |
| ('unisolar', 'gbm', 1)    |            6.53 |           0.27 |                  12.29 |                  0.08 |
| ('unisolar', 'gbm', 24)   |            7.45 |           0.06 |                  10.38 |                  0.06 |
| ('unisolar', 'ridge', 1)  |            9.81 |           0.07 |                  12.29 |                  0.08 |
| ('unisolar', 'ridge', 24) |            8.2  |           0.04 |                  10.38 |                  0.06 |

## RQ2/RQ3 Adaptation family: drift-region coverage, width, interval score
Static baseline vs windowed / ACI / AgACI competitors. Drift-PICP target 0.90; lower interval score is better.

|                           |   static_drift_PICP_mean |   static_drift_PICP_std |   static_PINAW_mean |   static_PINAW_std |   static_interval_score_mean |   static_interval_score_std |   windowed_drift_PICP_mean |   windowed_drift_PICP_std |   windowed_PINAW_mean |   windowed_PINAW_std |   windowed_interval_score_mean |   windowed_interval_score_std |   adaptive_drift_PICP_mean |   adaptive_drift_PICP_std |   adaptive_PINAW_mean |   adaptive_PINAW_std |   adaptive_interval_score_mean |   adaptive_interval_score_std |   agaci_drift_PICP_mean |   agaci_drift_PICP_std |   agaci_PINAW_mean |   agaci_PINAW_std |   agaci_interval_score_mean |   agaci_interval_score_std |
|:--------------------------|-------------------------:|------------------------:|--------------------:|-------------------:|-----------------------------:|----------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|---------------------------:|--------------------------:|----------------------:|---------------------:|-------------------------------:|------------------------------:|------------------------:|-----------------------:|-------------------:|------------------:|----------------------------:|---------------------------:|
| ('opsd', 'gbm', 1)        |                    0.468 |                   0.029 |               0.061 |                  0 |                    14029     |                    1216.52  |                      0.885 |                     0.005 |                 0.13  |                0.009 |                       8477.62  |                       484.403 |                      0.9   |                     0.002 |                 0.134 |                0.009 |                       8199.88  |                       503.954 |                   0.895 |                  0.003 |              0.128 |             0.007 |                    8086.87  |                    497.593 |
| ('opsd', 'gbm', 24)       |                    0.698 |                   0.012 |               0.124 |                  0 |                    14605.8   |                     322.973 |                      0.901 |                     0.012 |                 0.171 |                0.004 |                      12717.7   |                       289.35  |                      0.891 |                     0.004 |                 0.187 |                0.007 |                      13131.6   |                       469.358 |                   0.88  |                  0.005 |              0.184 |             0.005 |                   13447.9   |                    439.667 |
| ('opsd', 'ridge', 1)      |                    0.8   |                   0.019 |               0.194 |                  0 |                    16110.8   |                     278.781 |                      0.896 |                     0.002 |                 0.234 |                0.005 |                      15081.1   |                       193.477 |                      0.902 |                     0.001 |                 0.237 |                0.005 |                      14613.1   |                       293.62  |                   0.896 |                  0     |              0.226 |             0.002 |                   14201.5   |                    235.341 |
| ('opsd', 'ridge', 24)     |                    0.923 |                   0.002 |               0.376 |                  0 |                    22497.1   |                      19.4   |                      0.9   |                     0.001 |                 0.359 |                0     |                      22555.5   |                        14.023 |                      0.899 |                     0.001 |                 0.382 |                0.001 |                      24002.6   |                        15.954 |                   0.9   |                  0.001 |              0.359 |             0     |                   22599.5   |                     14.023 |
| ('uci', 'gbm', 1)         |                    0.216 |                   0.004 |               0.087 |                  0 |                       10.653 |                       1.897 |                      0.863 |                     0.013 |                 0.184 |                0.019 |                          4.703 |                         0.41  |                      0.899 |                     0.003 |                 0.191 |                0.02  |                          4.618 |                         0.39  |                   0.899 |                  0.003 |              0.191 |             0.02  |                       4.614 |                      0.39  |
| ('uci', 'gbm', 24)        |                    0.278 |                   0.008 |               0.113 |                  0 |                       10.28  |                       1.524 |                      0.866 |                     0.013 |                 0.21  |                0.02  |                          5.37  |                         0.406 |                      0.899 |                     0.002 |                 0.227 |                0.024 |                          5.505 |                         0.449 |                   0.896 |                  0.001 |              0.219 |             0.017 |                       5.353 |                      0.394 |
| ('uci', 'ridge', 1)       |                    0.263 |                   0.003 |               0.103 |                  0 |                       10.47  |                       1.566 |                      0.865 |                     0.01  |                 0.196 |                0.019 |                          5.131 |                         0.416 |                      0.9   |                     0.002 |                 0.205 |                0.021 |                          5.008 |                         0.404 |                   0.9   |                  0.002 |              0.205 |             0.021 |                       5.011 |                      0.403 |
| ('uci', 'ridge', 24)      |                    0.358 |                   0.006 |               0.123 |                  0 |                        8.953 |                       1.007 |                      0.869 |                     0.001 |                 0.212 |                0.018 |                          5.568 |                         0.461 |                      0.897 |                     0.002 |                 0.232 |                0.02  |                          5.691 |                         0.43  |                   0.898 |                  0.001 |              0.225 |             0.022 |                       5.557 |                      0.457 |
| ('unisolar', 'gbm', 1)    |                    0.951 |                   0.002 |               0.39  |                  0 |                       55.077 |                       0.229 |                      0.89  |                     0.002 |                 0.293 |                0.006 |                         52.932 |                         0.683 |                      0.897 |                     0.003 |                 0.308 |                0.004 |                         52.738 |                         0.598 |                   0.896 |                  0     |              0.304 |             0.007 |                      52.403 |                      0.572 |
| ('unisolar', 'gbm', 24)   |                    0.958 |                   0.001 |               0.544 |                  0 |                       69.587 |                       1.721 |                      0.907 |                     0     |                 0.391 |                0.016 |                         65.256 |                         2.721 |                      0.902 |                     0.003 |                 0.408 |                0.018 |                         68.953 |                         2.81  |                   0.895 |                  0.002 |              0.416 |             0.014 |                      69.738 |                      3.083 |
| ('unisolar', 'ridge', 1)  |                    0.981 |                   0.001 |               0.518 |                  0 |                       61.313 |                       0.273 |                      0.911 |                     0.002 |                 0.417 |                0.009 |                         56.39  |                         0.997 |                      0.897 |                     0.002 |                 0.405 |                0.011 |                         56.55  |                         0.998 |                   0.897 |                  0.002 |              0.406 |             0.011 |                      56.442 |                      0.992 |
| ('unisolar', 'ridge', 24) |                    0.967 |                   0.003 |               0.547 |                  0 |                       66.503 |                       1.236 |                      0.906 |                     0.003 |                 0.39  |                0.014 |                         61.338 |                         2.414 |                      0.9   |                     0     |                 0.402 |                0.019 |                         63.781 |                         2.686 |                   0.901 |                  0.001 |              0.393 |             0.016 |                      62.235 |                      2.033 |

Paired-bootstrap fraction where each method's drift coverage differs significantly from static:

|                           |   rq3_windowed_significant |   rq3_adaptive_significant |   rq3_agaci_significant |
|:--------------------------|---------------------------:|---------------------------:|------------------------:|
| ('opsd', 'gbm', 1)        |                          1 |                          1 |                       1 |
| ('opsd', 'gbm', 24)       |                          1 |                          1 |                       1 |
| ('opsd', 'ridge', 1)      |                          1 |                          1 |                       1 |
| ('opsd', 'ridge', 24)     |                          1 |                          1 |                       1 |
| ('uci', 'gbm', 1)         |                          1 |                          1 |                       1 |
| ('uci', 'gbm', 24)        |                          1 |                          1 |                       1 |
| ('uci', 'ridge', 1)       |                          1 |                          1 |                       1 |
| ('uci', 'ridge', 24)      |                          1 |                          1 |                       1 |
| ('unisolar', 'gbm', 1)    |                          1 |                          1 |                       1 |
| ('unisolar', 'gbm', 24)   |                          1 |                          1 |                       1 |
| ('unisolar', 'ridge', 1)  |                          1 |                          1 |                       1 |
| ('unisolar', 'ridge', 24) |                          1 |                          1 |                       1 |

## Equivalence to nominal (practical calibration)
Fraction of cells whose block-bootstrap drift-coverage CI lies entirely within [0.90±δ] — superiority over static is not the same as being *practically calibrated*.

|                  |   fraction_calibrated |
|:-----------------|----------------------:|
| static_equiv02   |                  0    |
| static_equiv05   |                  0.08 |
| windowed_equiv02 |                  0.08 |
| windowed_equiv05 |                  0.79 |
| adaptive_equiv02 |                  0.42 |
| adaptive_equiv05 |                  1    |
| agaci_equiv02    |                  0.46 |
| agaci_equiv05    |                  0.96 |

## RQ4/RQ6 Detection: label-free explanation trigger vs residual trigger
Lead = steps the trigger fires before static coverage visibly breaks (positive = early warning). Explanation signal is label-free.

|                           |   page_hinkley_FAR_mean |   page_hinkley_FAR_std |   page_hinkley_lead_mean |   page_hinkley_lead_std |   explanation_shift_FAR_mean |   explanation_shift_FAR_std |   explanation_shift_lead_mean |   explanation_shift_lead_std |
|:--------------------------|------------------------:|-----------------------:|-------------------------:|------------------------:|-----------------------------:|----------------------------:|------------------------------:|-----------------------------:|
| ('opsd', 'gbm', 1)        |                   0.991 |                  0.002 |                     79.5 |                  91.799 |                        0.01  |                       0.001 |                          26   |                       35.796 |
| ('opsd', 'gbm', 24)       |                   0.96  |                  0.009 |                    209   |                 241.332 |                        0.007 |                       0     |                        -202   |                      632.776 |
| ('opsd', 'ridge', 1)      |                   0.996 |                  0.001 |                    644   |                 733.235 |                      nan     |                     nan     |                         nan   |                      nan     |
| ('opsd', 'ridge', 24)     |                   0.978 |                  0.001 |                    357   |                 152.42  |                      nan     |                     nan     |                         nan   |                      nan     |
| ('uci', 'gbm', 1)         |                   0     |                  0     |                    -23   |                   9.238 |                        0.021 |                       0.001 |                          -5   |                       31.177 |
| ('uci', 'gbm', 24)        |                   0     |                  0     |                    -38.5 |                   0.577 |                        0.015 |                       0     |                          -3.5 |                        5.196 |
| ('uci', 'ridge', 1)       |                   0     |                  0     |                    -14   |                   6.928 |                      nan     |                     nan     |                         nan   |                      nan     |
| ('uci', 'ridge', 24)      |                   0     |                  0     |                    -35.5 |                   2.887 |                      nan     |                     nan     |                         nan   |                      nan     |
| ('unisolar', 'gbm', 1)    |                   0.449 |                  0.07  |                   1067.5 |                 246.529 |                        0.002 |                       0.002 |                         998   |                      166.277 |
| ('unisolar', 'gbm', 24)   |                   0.541 |                  0.107 |                   1044.5 |                 246.529 |                        0     |                       0     |                         nan   |                      nan     |
| ('unisolar', 'ridge', 1)  |                   0.596 |                  0.033 |                   1048   |                 235.559 |                      nan     |                     nan     |                         nan   |                      nan     |
| ('unisolar', 'ridge', 24) |                   0.554 |                  0.076 |                   1044.5 |                 246.529 |                      nan     |                     nan     |                         nan   |                      nan     |

## RQ5 coverage-before-accuracy (steps, >0 = coverage first) & RQ7 fidelity (>1 = faithful)
|                           |   rq5_cov_before_acc_mean |   rq5_cov_before_acc_std |   fidelity_ratio_mean |   fidelity_ratio_std |
|:--------------------------|--------------------------:|-------------------------:|----------------------:|---------------------:|
| ('opsd', 'gbm', 1)        |                    -309   |                   346.41 |                  4.11 |                 0.38 |
| ('opsd', 'gbm', 24)       |                       4   |                     1.15 |                  2.43 |                 0.6  |
| ('opsd', 'ridge', 1)      |                    -950.5 |                  1015.56 |                nan    |               nan    |
| ('opsd', 'ridge', 24)     |                     105   |                     5.77 |                nan    |               nan    |
| ('uci', 'gbm', 1)         |                      36   |                     2.31 |                  3.7  |                 2    |
| ('uci', 'gbm', 24)        |                      52.5 |                    54.85 |                  1.38 |                 0.36 |
| ('uci', 'ridge', 1)       |                      13   |                    17.32 |                nan    |               nan    |
| ('uci', 'ridge', 24)      |                      20.5 |                    15.59 |                nan    |               nan    |
| ('unisolar', 'gbm', 1)    |                       0   |                     0    |                  2.64 |                 0.04 |
| ('unisolar', 'gbm', 24)   |                      13.5 |                    13.28 |                  4.68 |                 0.32 |
| ('unisolar', 'ridge', 1)  |                     inf   |                   nan    |                nan    |               nan    |
| ('unisolar', 'ridge', 24) |                     -36   |                    41.57 |                nan    |               nan    |

## Backbone comparison (Wilcoxon signed-rank on MAE)
- gbm mean MAE 587 vs ridge 1.12e+03; lower/better = **gbm**; p = 0.0001608 (n=24 configs)
