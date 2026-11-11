# Registration: NAI's formula network (nai_cli --net) as the expected-power model of wind turbines

Registered 2026-11-09, before any model was run on the test year. The fingerprint is the SHA-256 of
`docs/prereg/FNET_WIND.manifest`. Earlier registrations of the same experiment (experiment 10): `FNET_NICHE.md`,
`FNET_FRESH.md`, `FNET_THIRD.md`, `FNET_FOURTH.md`, `FNET_ROBOT.md`, `FNET_MOTOR.md`.

## Question

A wind turbine's controller and its operator compare the power produced with the power expected from the wind; a
gap reveals icing, pitch or yaw faults and underperformance. The industry's expected power is the turbine's power
curve (IEC 61400-12-1: power against density-normalised wind speed). Does NAI's formula network, learning what the
power curve misses (turbulence, yaw misalignment, wind direction, air density), predict the power of the next year
better than the power curve and a small neural network, close to tuned gradient boosting, with C code an order of
magnitude smaller and faster than boosting's?

## Data

Penmanshiel wind farm data (Cubico Sustainable Investments; Zenodo 10.5281/zenodo.16807304, CC BY 4.0), turbines
WT11-WT15 (Senvion MM82, 2050 kW), 10-minute SCADA: `Penmanshiel_SCADA_2018_WT11-15_3116.zip` (md5
7c40dc00df6d6301427213e15170b927) and `Penmanshiel_SCADA_2019_WT11-15_3117.zip` (md5 92747a976716c5f35d9ee6462958fd7a).
Tables by `fnet/stand/wind_prepare.py` (rules in its header; SHA-256 in `fnet/data/wind_tables.tsv`): normal operation
(data available, no curtailment or derating, not stopped). Train = 2018-04-05 to 2018-12-31 (33 103-34 646 rows per
turbine); test = 2019 (50 931-51 504 rows per turbine).

## Formulation (chosen on 2018 only)

Inputs: wind speed, its 10-minute standard deviation, the yaw misalignment, sin and cos of the wind direction, the
nacelle ambient temperature; target: power (kW). One model per turbine. **fnet_res**: the IEC power curve fitted on
the same training rows is the nominal model and the network learns its error (inputs: the six and the curve's value);
the prediction is the curve plus the network.

Development (`fnet/stand/wind_run.py --side dev`: fit 2018-04-05..09-30, check 2018-10-01..12-31; 3 tries, logs
`D:/Claude/nai-data/fnet/wind/dev*.log`): fnet on the power directly, mean NRMSE 3.37 % (IEC curve 3.33, MLP 4.09,
tuned LightGBM 2.39); fnet on the curve's error 2.66 %; the same on every row instead of every 2nd 2.63 %. Chosen:
fnet_res, every 2nd row.

## Models (one run each; `fnet/stand/run_wind_test.sh`; every model fits every 2nd training row)

- **fnet_res**: `nai_cli --net` of NAI v26 (`bench/results/v26/nai_cli_v26.exe`; network v13, released settings), 120 s,
  4 threads, seed 1; its `--export-c` C code (the curve, a table of about 50 bin values, runs beside it).
- **iec**: the power curve: wind speed normalised to the training mean air density (rho ~ 1/T), 0.5 m/s bins of at
  least 3 rows, linear interpolation between bin centres.
- **lightgbm_tuned**: random search over 20 settings, 3-fold check grouped by calendar week; C by `robot_run.lgbm_c`.
- **mlp32**: `competitors.mlp(32)`; C by `competitors.mlp_c`.

## Measure

Per turbine: RMSE of the power (kW) on the test year, NRMSE = RMSE / 2050 kW; the energy error = sum of predicted
over sum of measured power minus 1. A model's value: the mean over the five turbines. C size and time: per turbine on
about 5 000 test points (gcc -O2, double). Computed by `fnet/stand/wind_hypotheses.py`.

## Hypotheses

- **H1 (against the industry's power curve):** fnet's mean NRMSE is below the IEC curve's.
- **H2 (against boosting):** fnet's mean NRMSE is at most 1.15 x tuned LightGBM's.
- **H3 (against a small network):** fnet's mean NRMSE is below MLP 32x32's.
- **H4 (C code):** over the turbines, the median of LightGBM's size / fnet's and of LightGBM's time / fnet's are both at
  least 10, and fnet's compiled outputs equal its own to the bit on every turbine.
- **H5 (energy):** fnet's mean absolute energy error is below the IEC curve's.

Each hypothesis holds or fails as computed; no correction, no re-run. Expectations from development (autumn 2018, a
shorter and different season than a whole year): fnet 2.66 %, LightGBM 2.39 % (ratio 1.11), IEC 3.33 %, MLP 4.09 %;
energy errors: fnet 0.43 %, IEC 2.12 %; C: fnet 14-16 KB and 0.25-0.4 us, LightGBM 0.16-1.1 MB and 4-36 us.

## Rules

- One look: `run_wind_test.sh` runs once, start to end; its outputs are kept as they are. A failure is reported as
  such and not repeated with other settings.
- Nothing in the registered files changes after the fingerprint; a deviation goes to `FNET_WIND-deviation.md` before
  the results are read.
- Publication on the site is decided by the user afterwards ("publish only if NAI is on par with the leaders").
