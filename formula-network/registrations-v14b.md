# NAI-fnet v14b: two tests registered before their runs

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
