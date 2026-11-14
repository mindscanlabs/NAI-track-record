# Registration: NAI's formula network v14b as the expected-power model of wind turbines, a second wind farm

Registered 2026-11-14, before any model was run on the test year. The fingerprint is the SHA-256 of
`docs/prereg/FNET_WIND2.manifest`; it is published in the NAI track record before the run. This is the second test of
the same question as `FNET_WIND.md` (Penmanshiel, run 2026-11-09: H1-H4 held, H5 failed: the IEC power curve's yearly
energy error was smaller), on a farm that no part of the development has seen, with the network's next version.

## Question

A wind turbine's controller and its operator compare the power produced with the power expected from the wind; a gap
reveals icing, pitch or yaw faults and underperformance. The industry's expected power is the turbine's power curve
(IEC 61400-12-1: power against density-normalised wind speed). Does NAI's formula network v14b (`nai_cli --net`),
learning what the power curve misses, predict the power of the next year better than the power curve and a small neural
network, close to tuned gradient boosting, with C code an order of magnitude smaller and faster than boosting's; and is
its yearly energy error now smaller than the power curve's?

## Data

Hill of Towie wind farm open dataset (RES on behalf of TRIG; Zenodo 10.5281/zenodo.22662930, version 2.1.0, CC BY 4.0),
21 Siemens SWT-2.3-VS-82 turbines (2300 kW, hub 59 m, rotor 82 m), 10-minute SCADA: `2018.zip` (md5
5d3a77aa05c75ea8476cc279a24d48ac) and `2019.zip` (md5 ca240b179200f5db25a273a1291eb597), both as listed by the Zenodo
record. A power prediction challenge (WeDoWind) has used this dataset, so public analyses of it exist; none was read for
this test. Tables by `fnet/stand/wind2_prepare.py` (rules in its header; SHA-256 in `fnet/data/wind2_tables.tsv`):
normal operation (in operation for the whole 10 minutes, no stop, the power setpoint at the rated 2300 kW at the end of
the period and of the previous one, power above 20 kW whenever the wind exceeds 4 m/s). Before the rules were fixed,
only the 2018 distributions of the status times and of the setpoint were looked at, not the power. Train = 2018, test =
2019, all 21 turbines (T16 and T17 are derated more often and keep fewer rows: 6 926 and 20 024 training rows; they stay
in, no threshold was set).

## Formulation (the Penmanshiel test's, not re-chosen)

Inputs: wind speed (active sensor), its 10-minute standard deviation, sin and cos of the nacelle position (the wind
direction field starts only in 2022), the ambient temperature; target: power (kW). One model per turbine. **fnet_res**:
the IEC power curve fitted on the same training rows is the nominal model and the network learns its error (inputs: the
five and the curve's value); the prediction is the curve plus the network; every model fits every 2nd training row. The
Penmanshiel test had a sixth input, the yaw misalignment; these data have no such field.

Development on 2018 only (`wind2_run.py --side dev`: fit 2018-01-01..09-30, check 2018-10-01..12-31; one run, no choice
made from it; logs `D:/Claude/nai-data/fnet/wind2/dev.log`): mean NRMSE fnet_res 2.004 %, IEC curve 2.259 %, tuned
LightGBM 1.913 % (ratio 1.05), MLP 2.298 %; mean absolute energy error fnet_res 0.78 %, IEC 1.05 %, LightGBM 0.78 %,
MLP 0.71 %; C: fnet 12.0 KB and 0.30 us, LightGBM 512 KB and 13.7 us (medians over turbines), fnet's C equal to its
predictions on every turbine. These are the expectations; the check quarter is a shorter and different season than a
whole year, and at Penmanshiel the energy error on the development quarter (0.43 % against 2.12 %) did not carry over
to the test year (0.40 % against 0.22 %).

## Models (one run each; `fnet/stand/run_wind2_test.sh`)

- **fnet_res**: `nai_cli --net` of `fnet/build/v14b/nai_cli_v14b.exe` (network v14b, released settings), 120 s, 4
  threads, seed 1; its `--export-c` C code (the curve, a table of about 50 bin values, runs beside it).
- **iec**: the power curve: wind speed normalised to the training mean air density (rho ~ 1/T), 0.5 m/s bins of at
  least 3 rows, linear interpolation between bin centres.
- **lightgbm_tuned**: random search over 20 settings, 3-fold check grouped by calendar week; C by `robot_run.lgbm_c`.
- **mlp32**: `competitors.mlp(32)`; C by `competitors.mlp_c`.

## Measure

Per turbine: RMSE of the power (kW) on the test year, NRMSE = RMSE / 2300 kW; the energy error = sum of predicted over
sum of measured power minus 1. A model's value: the mean over the 21 turbines. C size and time: per turbine on about
5 000 test points (gcc -O2, double). Computed by `fnet/stand/wind2_hypotheses.py`.

## Hypotheses (the Penmanshiel test's five)

- **H1 (against the industry's power curve):** fnet's mean NRMSE is below the IEC curve's.
- **H2 (against boosting):** fnet's mean NRMSE is at most 1.15 x tuned LightGBM's.
- **H3 (against a small network):** fnet's mean NRMSE is below MLP 32x32's.
- **H4 (C code):** over the turbines, the median of LightGBM's size / fnet's and of LightGBM's time / fnet's are both at
  least 10, and fnet's compiled outputs equal its own to the bit on every turbine.
- **H5 (energy):** fnet's mean absolute energy error is below the IEC curve's.

Each hypothesis holds or fails as computed; no correction, no re-run.

## Rules

- One look: `run_wind2_test.sh` runs once, start to end; its outputs are kept as they are. A failure is reported as
  such and not repeated with other settings.
- Nothing in the registered files changes after the fingerprint; a deviation goes to `FNET_WIND2-deviation.md` before
  the results are read.
- Publication is decided by the user afterwards ("publish only if NAI is on par with the leaders").
