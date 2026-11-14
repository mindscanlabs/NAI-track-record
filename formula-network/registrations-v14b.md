# NAI-fnet v14b: two tests registered before their runs

Fingerprints published on 14 November 2026 (commit fcd6f68), before either test was run. Both tests ran once, the same
day, 02:18 to 08:52 UTC, without errors; before the start every file of both manifests was checked against the
fingerprints. Status: **scored**. The text published before the runs is kept unchanged below the results.

## Results

### Expected power of wind turbines, a second farm: 5 of 5

Hill of Towie, 21 turbines, trained on 2018, checked on 2019 (registration
[FNET_WIND2.md](registered/docs/prereg/FNET_WIND2.md); output [wind2_test_hypotheses.txt](results/wind2_test_hypotheses.txt)).

| model | NRMSE (mean over 21 turbines) | yearly energy error, mean of absolute values | C code (T01) |
|---|---|---|---|
| **NAI-fnet v14b** on top of the IEC power curve | 2.656 % | **1.98 %** | 9.7 KB, 0.30 µs |
| tuned LightGBM | **2.534 %** | 1.94 % | 1.07 MB, 35 µs |
| MLP 32x32 | 2.686 % | 1.95 % | 10.8 KB, 0.70 µs |
| IEC power curve | 2.874 % | 2.41 % | table |

H1 (below the power curve), H2 (at most 1.15 x tuned LightGBM: 1.05 x), H3 (below the MLP), H4 (LightGBM's C 43 x larger
and 63 x slower; NAI-fnet's C equal to its predictions on every turbine) and H5 (yearly energy error below the power
curve's, the hypothesis that failed at Penmanshiel) held. Every model, the power curve too, overestimated the energy of
2019 on most turbines (+1 to 2 %); on T15 and T19 every model was about 7 to 8 % high. On the energy error NAI-fnet beat
the power curve, but LightGBM and the MLP were level with it.

### Fifth suite of tables: 5 of 7

Seven new tables, 35 (table, split) pairs: 7 inside the data, 28 beyond its edge (registration
[FNET_FIFTH.md](registered/docs/prereg/FNET_FIFTH.md); outputs [fifth_test_hypotheses.txt](results/fifth_test_hypotheses.txt),
[fifth_test_compare.txt](results/fifth_test_compare.txt)). Relative RMSE (RMSE / RMSE of the training mean), medians
over the pairs:

| model | beyond the edge | inside | pairs worse than the mean | worst pair |
|---|---|---|---|---|
| **NAI-fnet v14b** | **0.378** | 0.440 | 4 | **1.85** |
| NAI-fnet v13 | 0.378 | 0.450 | 3 | 1.76 |
| EBM | 0.513 | 0.448 | 5 | 4.76 |
| MLP | 0.532 | 0.517 | 5 | 4.19 |
| tuned CatBoost | 0.554 | 0.391 | 5 | 9.23 |
| tuned LightGBM | 0.564 | **0.370** | 3 | 9.62 |

| hypothesis | result |
|---|---|
| H1 beyond the edge, at most tuned LightGBM | **held**: 0.378 vs 0.564 |
| H2 pairs worse than the mean, not more than tuned LightGBM | **failed**: 4 vs 3 |
| H3 inside, at most 1.5 x tuned LightGBM | **held**: 1.19 x |
| H4 compiled C, LightGBM at least 10 x larger and 3 x slower | **held**: 57 x and 8.5 x (medians over the tables) |
| H5 beyond the edge, at most 1.15 x MLP and EBM | **held**: better than both |
| H6 v14b against v13: geometric mean of the ratio at most 1.02 and not more pairs worse than the mean | **failed**: 0.9997, but 4 vs 3 |
| H7 the range monitor: error far beyond the data above the error near it, in at least 2/3 of the pairs | **held**: 6 of 7 |

One pair decided H2 and H6: on the upper tail of the composite curing distortion no model beat the training mean
(NAI-fnet v14b 1.0004, v13 1.0000, tuned LightGBM 0.997). The other three pairs where NAI-fnet was worse than the
mean are all from the laser powder bed fusion compilation (1.14, 1.25, 1.85; tuned LightGBM about 1.0 there), a noisy
compilation of published data whose material column the registered cleaning rules removed. Tuned LightGBM's worst pair
was the lower tail of the curing distortion, 9.6, where NAI-fnet was nearly exact (0.001). Version v14b was aimed at
fewer failures on noisy data; on these new data it is level with v13 (geometric mean 0.9997), as its development
material had predicted (0.996), and the aim was not reached.

### What is published

The registrations, their manifests and the harness scripts, byte for byte, in [`registered/`](registered/), under
the paths of the manifests; the outputs in [`results/`](results/). Not published, as for the earlier tests: the
program's binaries and source, and four development harness files that call or configure the program; their SHA-256
are in the manifests.

---

## Published before the runs (unchanged)

Published on 14 November 2026, before either test was run. Each fingerprint is the SHA-256 of a manifest that lists
the SHA-256 of the registration document and of every file the test rests on: the data tables and splits, the harness
scripts and the program's binary. The registration documents, the manifests and the results will be published here
after the runs, whatever the results; anyone can then check them against the fingerprints below.

| test | data (never used in the development) | hypotheses | fingerprint (SHA-256) |
|---|---|---|---|
| fifth suite of tables | 7 open engineering and physical tables in the product's scope: aerodynamic drag (CFD), wall U-value (FE), composite curing distortion (FE), cellular steel beams (FE), superconducting wire critical current (laboratory), hydrogen solubility in zirconium alloys and laser powder bed fusion density (two noisy compilations of published data) | 7: against tuned LightGBM beyond the edge of the data, reliability and inside the data; against MLP and EBM; compiled C; against the previous version v13; whether the error grows with the range monitor's distance | `614fe99cae489e2125a119ab8bda64f5a44984eeec1141472a07a6a57314c67f` |
| expected power of wind turbines, a second farm | Hill of Towie wind farm (RES; Zenodo 10.5281/zenodo.22662930, CC BY 4.0), 21 turbines, train 2018, test 2019 | 5, the same as for the Penmanshiel test: against the IEC power curve, tuned LightGBM and an MLP; compiled C; the yearly energy error against the power curve's (the hypothesis that failed at Penmanshiel) | `5e9b60a275fb315ccf8f713d1ace76ef9c09883f1e1782e8b2c52cc804a194da` |

Version: NAI-fnet v14b, the network after v13 (the version of the preprint, DOI
[10.5281/zenodo.24163946](https://doi.org/10.5281/zenodo.24163946)). Each test runs once, start to end; each hypothesis
holds or fails as computed, with no re-run; a deviation, if any, is written down before the results are read.
