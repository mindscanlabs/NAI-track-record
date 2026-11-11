# Registration: NAI's formula network (nai_cli --net) as the aerodynamic model of a transport aircraft

Registered 2026-11-10, before any model was run on the test points. The fingerprint is the SHA-256 of
`docs/prereg/FNET_AIRCRAFT.manifest`. Earlier registrations of the same experiment (experiment 10): `FNET_NICHE.md`,
`FNET_FRESH.md`, `FNET_THIRD.md`, `FNET_FOURTH.md`, `FNET_ROBOT.md`, `FNET_MOTOR.md`, `FNET_WIND.md`.

## Question

A flight computer's performance and control functions hold an aircraft's aerodynamic coefficients as multi-dimensional
look-up tables over angle of attack, Mach and other variables. Does NAI's formula network, trained on wind-tunnel
measurements of a modern transport, predict lift, drag and pitching moment better than such a table and than tuned
gradient boosting, in particular beyond the measured Mach range, where drag rises steeply (the drag divergence),
with C code an order of magnitude smaller than boosting's?

## Data

NASA Common Research Model (a generic wide-body transport), National Transonic Facility Test 197 (2010), posted at
commonresearchmodel.larc.nasa.gov (`NTF197Data.zip`, SHA-256 6f2ef0d10c4e2f1b037461f874ed7f055d39ccab6985e331e45d7146da1ca95d;
`TWICSCorr`: wall-interference corrected). A US Government work; NASA is acknowledged as the source and endorses
nothing here. Table by `fnet/stand/aircraft_prepare.py` (rules in its header; SHA-256 in `fnet/data/aircraft_tables.tsv`):
the wing-body-tail configuration, tail incidence -2, 0, +2 deg; inputs AWALL (corrected angle of attack), MWALL
(corrected Mach), CREYN (Reynolds number, millions), QINFFT (dynamic pressure: the wing's elastic deflection), CONFT
(tail incidence); targets CLWALL, CDWALL, CMWALL. Sides by whole runs: **train** 659 points (35 runs, Mach 0.70-0.85),
**test_inside** 155 points (8 runs: every 5th run at Mach 0.85 and below), **test_edge** 225 points (9 runs at Mach
0.86-0.87, beyond the training range).

## Formulation (development on the training runs only)

One model per coefficient on the five inputs. Development (`fnet/stand/aircraft_run.py --side dev`: the training runs
at Mach 0.85 as the edge check, every 4th other run as the inside check, 309 points to fit; one formulation, one try,
log `D:/Claude/nai-data/fnet/aircraft/dev1.log`): CD inside / edge in drag counts (1e-4): fnet 18.2 / 68.2, tuned
LightGBM 38.4 / 99.3, MLP 32x32 21.8 / 156.6, table 44.4 / 169.2; CL edge: fnet 0.029, LightGBM 0.043, MLP 0.106,
table 0.095; CM edge: fnet 0.0299, LightGBM 0.0292.

## Models (one run each; `fnet/stand/run_aircraft_test.sh`)

- **NAI-fnet**: `nai_cli --net` of NAI v26 (`bench/results/v26/nai_cli_v26.exe`; network v13, released settings), 120 s,
  4 threads, seed 1; its `--export-c` C code.
- **table**: a look-up table as in flight software: for each Reynolds group and tail incidence of the training
  points, linear interpolation over (alpha, Mach); the nearest training point outside their hull (no extrapolation).
- **lightgbm_tuned**: random search over 20 settings, 3-fold check grouped by run; C by `robot_run.lgbm_c`.
- **mlp32**: `competitors.mlp(32)`; C by `competitors.mlp_c`.

## Measure

RMSE per coefficient on test_inside and on test_edge (CD also in drag counts); C size and time (gcc -O2, double) on
all test points. Computed by `fnet/stand/aircraft_hypotheses.py`.

## Hypotheses

- **H1 (drag beyond the edge, against the table):** fnet's CD RMSE on test_edge is below the table's.
- **H2 (drag beyond the edge, against boosting):** fnet's CD RMSE on test_edge is at most tuned LightGBM's.
- **H3 (lift beyond the edge):** fnet's CL RMSE on test_edge is at most tuned LightGBM's.
- **H4 (drag inside):** fnet's CD RMSE on test_inside is at most 1.15 x tuned LightGBM's.
- **H5 (C code):** for each of the three coefficients LightGBM's C code is at least 10 x larger than fnet's, and fnet's
  compiled outputs equal its own to the bit.

Each hypothesis holds or fails as computed; no correction, no re-run. Expectations from development (fewer points to
fit, an edge only 0.01-0.02 Mach beyond, against 0.01-0.02 Mach in the test as well): the values above; the test's
models fit 659 points. The pitching moment is reported, not tested.

## Rules

- One look: `run_aircraft_test.sh` runs once, start to end; its outputs are kept as they are. A failure is reported as
  such and not repeated with other settings.
- Nothing in the registered files changes after the fingerprint; a deviation goes to `FNET_AIRCRAFT-deviation.md`
  before the results are read.
- Publication on the site is decided by the user afterwards ("publish only if NAI is on par with the leaders").
