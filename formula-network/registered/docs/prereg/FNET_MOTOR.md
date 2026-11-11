# Registration: NAI's formula network (nai_cli --net) as a virtual rotor-temperature sensor of a traction motor

Registered 2026-11-09, before any model was run on the test profiles. The fingerprint is the SHA-256 of
`docs/prereg/FNET_MOTOR.manifest`. Earlier registrations of the same experiment (experiment 10): `FNET_NICHE.md`,
`FNET_FRESH.md`, `FNET_THIRD.md`, `FNET_FOURTH.md`, `FNET_ROBOT.md`.

## Question

The permanent magnets of a traction motor must not overheat, but a sensor on the rotating rotor is impractical in a
production drive; the inverter has the currents, voltages, speed, the coolant temperature and thermistors in the
stator. Does NAI's formula network, given those signals and their moving averages, estimate the rotor temperature
as well as a small neural network, much better than tuned gradient boosting and a linear model, with C code smaller
than boosting's?

## Data

Electric Motor Temperature (W. Kirchgaessner, O. Wallscheid, J. Boecker, Paderborn University; Kaggle version 3,
DOI 10.34740/KAGGLE/DSV/2161054, CC BY-SA 4.0): a permanent magnet synchronous motor on a test bench, 69 profiles,
185 hours at 2 Hz. Archive SHA-256 10e49e6220fa3c8a9d22c8bab8280ffe2d5e1e3380a6a18bcfc64ea2e8b56b92; the per-profile
tables are built by `fnet/stand/motor_prepare.py` (their SHA-256 in `fnet/data/motor_tables.tsv`).

Sides: **test** = profiles 60, 62, 74 (8.9 hours; the authors' generalization set for this version of the data,
Thermal Neural Networks, Engineering Applications of AI 117 (2023) 105537); **dev** = 58, 65, 72 (their validation and
test profiles of the earlier, 140-hour version); **train** = the other 63 profiles. For the test, the models train on
train + dev (66 profiles), every 60th sample (one row every 30 s, 21 149 rows); the checks use every sample.

## Formulation (chosen on the train and dev profiles only)

Inputs (67): the 7 measured signals (ambient, coolant, u_d, u_q, i_d, i_q, motor speed) and 5 derived ones (|u|, |i|,
S_el = 1.5 |u| |i|, |i| speed, S_el speed), each as is and as exponentially weighted moving averages with spans 500,
2161, 4000, 8895 samples (the spans the authors' search found for the rotor, IEEE TPEL 36(7) 2021), computed per
profile from its first sample; and the three measured stator temperatures (yoke, tooth, winding) with the moving
averages of the winding temperature (same spans). Target: pm, the rotor temperature (deg C).

Development (`fnet/stand/motor_run.py --side dev`; 4 formulations tried, logs `D:/Claude/nai-data/fnet/motor/dev*.log`):
the 60 signal features alone: fnet 26.2 K^2, MLP 21.5 (every model failed at the profiles' start: the stator's state is
unknown); with the stator temperatures (67 inputs): fnet 4.91, MLP 32x32 4.73, ridge 11.7, tuned LightGBM 15.0;
24 compact inputs: fnet 22.7, MLP 28.7; 67 inputs at three times the rows: fnet 5.54, MLP 5.41. Chosen: 67 inputs,
every 60th sample. The largest errors of every model fall in the first seconds of a profile, where the moving
averages start from the instantaneous values (in a drive they run continuously); hence the second error measure below.

## Models (one run each; `fnet/stand/run_motor_test.sh`)

- **NAI-fnet**: `nai_cli --net` of NAI v26 (`bench/results/v26/nai_cli_v26.exe`; network v13, `src/Net/FormulaNet.cpp`,
  released settings `kReleaseFlags`), 120 s, 4 threads, seed 1; its `--export-c` C code.
- **MLP 32x32**: scaled inputs and target, two ReLU layers, early stopping (`competitors.mlp(32)`); C by `competitors.mlp_c`.
- **Ridge**: standardised inputs, the penalty chosen by leave-one-out among 19 values (RidgeCV), written back to the
  raw inputs; C: one dot product.
- **Tuned LightGBM**: random search over 20 settings, 3-fold check grouped by profile; C by `robot_run.lgbm_c`.
- **Compiled size and speed**: `size.compile_and_measure` (gcc -O2, double) on about 5 000 check points; the moving
  averages are computed by the drive's software for every model alike and are not counted.

## Measure

MSE (K^2) over all test samples (as in the authors' papers); the largest absolute error (K) over all samples and over
the samples after the first 10 minutes of each profile. Computed by `fnet/stand/motor_hypotheses.py`.

## Hypotheses

- **H1 (against a small network):** fnet's MSE is at most 1.15 x MLP 32x32's.
- **H2 (against boosting):** fnet's MSE is at most 0.5 x tuned LightGBM's.
- **H3 (against a linear model):** fnet's MSE is below the ridge model's.
- **H4 (the worst case):** fnet's largest error after the first 10 minutes is at most 1.25 x MLP 32x32's.
- **H5 (C code):** fnet's C code is smaller than tuned LightGBM's and gives the model's numbers to the bit.

Each hypothesis holds or fails as computed; no correction, no re-run. Expectations from development (the dev
profiles): fnet 4.9 K^2, MLP 4.7, ridge 11.7, LightGBM 15.0; C: fnet 86 KB / 1.7 us, MLP 28 KB / 1.9 us, LightGBM
133 KB / 1.4 us. Context only, not comparable (different inputs): the authors' Thermal Neural Network on the same
three test profiles without stator inputs, rotor only: MSE 4.34 K^2, largest error 6.02 K.

## Rules

- One look: `run_motor_test.sh` runs once, start to end; its outputs are kept as they are. A failure is reported as
  such and not repeated with other settings.
- Nothing in the registered files changes after the fingerprint; a deviation goes to `FNET_MOTOR-deviation.md`
  before the results are read.
- Publication on the site is decided by the user afterwards ("publish only if NAI is on par with the leaders").
