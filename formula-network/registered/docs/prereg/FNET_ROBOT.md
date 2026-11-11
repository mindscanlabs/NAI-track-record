# Registration: NAI's formula network (nai_cli --net) as a virtual joint-torque sensor on a real robot arm

Registered 2026-11-09, before any model was run on the test trajectories. The fingerprint is the SHA-256 of
`docs/prereg/FNET_ROBOT.manifest`. Earlier registrations of the same experiment (experiment 10): `FNET_NICHE.md`,
`FNET_FRESH.md`, `FNET_THIRD.md`, `FNET_FOURTH.md`.

## Question

A robot joint controller needs the torque its motor must give (feed-forward control, collision detection). A
manufacturer has a nominal rigid-body model of the arm; what it misses (friction, cables, errors in the nominal masses)
is usually identified by hand or learned by a Gaussian process. On the published protocol of a real 7-joint arm, does
NAI's formula network, learning the nominal model's error, predict the joint torques as well as the authors' own
physics-informed Gaussian process, as well as tuned gradient boosting, better than a small MLP, with C code an order of
magnitude smaller and faster than boosting?

## Data

Robot Inverse Dynamics Dataset (Giacomuzzo, Dalla Libera, Romeres, MERL; Zenodo 12516500 v4, CC BY-SA 4.0; archive
`PUB-5510-LIP4RID.zip`, SHA-256 527ec997b8f957f102e07f132f2663156ffcfe9366ed1c9f1d6e14ad21409288), the real Franka Emika
Panda part: `Data/Robots/PANDA/Experiments/*_as_filtered_fcut4.0.pkl` (joint positions, velocities, accelerations,
torques) and `*_dynamics_components.pkl` (the nominal model's inertia matrix, Coriolis and gravity torques per sample).
The pickles are read by a restricted unpickler that accepts only the classes they were seen to name and builds no pandas
object (`fnet/stand/robot_prepare.py`); the tables' SHA-256 are in `fnet/data/robot_tables.tsv`.

Protocol of the reference paper (Giacomuzzo et al., "A Black-Box Physics-Informed Estimator based on Gaussian Process
Regression for Robot Inverse Dynamics Identification", IEEE Transactions on Robotics, 2024; their code
`RealData/PANDA/config/gen_config*.py`): training seeds 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 16, 18; combination c
(0-11) trains on the seeds at positions c and c + 1 of this list; test seeds 21, 22, 23, 25, 26, 27, 29, 30, 31, 32,
33, 34, 35, 36, 37, 38; every 10th sample of every file (`downsampling_data_load = 10`); target `tau_interp`. The archive
holds one training file per seed (`num_sin_50`); the authors' configs list two per seed (`num_sin_50` and `num_sin_100`),
so the models here train on about half the rows the authors' models had (about 586 rows per combination). The test
trajectories (`num_sin_100`) are richer motions than the training ones (`num_sin_50`).

## Formulation (chosen on the training seeds only)

One model per joint j. Inputs: q, dq, ddq of the 7 joints and sin q, cos q of each (35). Target: tau_interp_j -
tau_nom_j, where tau_nom = M(q) ddq + c(q, dq) + g(q) is the nominal model from the archive (`robot_nominal.py`);
the prediction is tau_nom_j + the model's output. The nominal model is a function of the inputs, computed from the
manufacturer-style nominal parameters, not fitted to any trajectory. The Gaussian processes of the paper do not use it.

Development (`robot_run.py --side dev`, `run_robot_dev.sh`, `run_robot_dev2.sh`; combinations 0 and 6, each checked on
the 11 training seeds it does not use): on the elbow (joint 4), fnet on the raw target gave nMSE 9.0 %, with sin, cos
25 %; on the residual target 0.042 % (21 inputs) and 0.043 % (35 inputs); all rows instead of every 10th: no gain. The
rule fixed before the second development run: the formulation with the lower mean nMSE of fnet over the 7 joints.
21 inputs: 2.242 %; 35 inputs: 2.159 %; so the 35 inputs.

## Models (one run each; `fnet/stand/run_robot_test.sh`)

- **NAI-fnet**: `nai_cli --net` of NAI v26 (`bench/results/v26/nai_cli_v26.exe`; network v13, `src/Net/FormulaNet.cpp`,
  released settings `kReleaseFlags`), 120 s, 4 threads, seed 1; its `--export-c` C code.
- **Tuned LightGBM**: random search over 20 settings, 3-fold check inside the training rows (`baselines.tuned`); C code
  by `robot_run.lgbm_c` (one function per tree).
- **MLP 32x32**: scaled inputs and target, two ReLU layers, early stopping (`competitors.mlp(32)`); C code by
  `competitors.mlp_c`.
- All three learn the same residual with the same inputs.
- **Reported baselines, not run here**: the authors' published estimates on the test trajectories, for every combination
  (`Data/Robots/PANDA/Results/*_estimates.pkl`): LIP GP (`LK_GIP_sum`, the paper's model), LSE GP (`LK_RBF_1_sc`), GIP GP
  with friction and RBF GP per joint; their Y equals tau_interp at every 10th sample (checked by `robot_hypotheses.py`).
  And the nominal model alone.
- **Compiled size and speed**: for combination 0 of every joint, `size.compile_and_measure` (gcc -O2, double; size =
  .text + .rdata + .data of the object file; ns per prediction over the test points, 200 repetitions), with the check
  of the compiled outputs against the model's own.

## Measure

nMSE (%) = 100 x mean squared error / variance of the measured torque, per test trajectory; a model's value for a joint
is the mean over the 12 combinations x 16 test trajectories (192 values), as in the paper. Computed by
`fnet/stand/robot_hypotheses.py`.

## Hypotheses

- **H1 (the elbow, against the paper's model):** fnet's nMSE on joint 4 is at most the LIP GP's.
- **H2 (the elbow, against boosting):** fnet's nMSE on joint 4 is at most 1.25 x tuned LightGBM's.
- **H3 (the elbow, against a small network):** fnet's nMSE on joint 4 is below MLP 32x32's.
- **H4 (compiled C, the elbow, combination 0):** LightGBM's C code is at least 10 x larger and at least 10 x slower per
  prediction than fnet's, and fnet's compiled outputs equal its own to the bit (max difference 0).
- **H5 (all joints, against the paper's model):** fnet's nMSE is below the LIP GP's on at least 5 of the 7 joints.

Each hypothesis holds or fails as computed; no correction, no re-run. Expectations from development (training seeds,
`num_sin_50` motions only, so likely optimistic): elbow fnet 0.043 %, tuned LightGBM 0.038 %, MLP 0.147 %; per joint fnet
0.22, 0.009, 0.084, 0.043, 4.8, 0.76, 9.2 %. The LIP GP's published test values are known before this run (0.49, 0.051,
0.29, 0.090, 10.4, 4.1, 5.8 % by `robot_baselines.py`); the development set has no LIP estimates, so H1 and H5 have no
development counterpart. Elbow C on development: fnet 33.8 KB, 417 ns; LightGBM 566 KB, 25.4 us. A dry run of
`robot_hypotheses.py` with no model results (to check the script) printed, before this registration, the test values of
the nominal model alone (0.71, 0.084, 0.66, 0.64, 46.0, 7.9, 102.5 %) and of the four GP models; no model of this
registration has been run on a test trajectory.

## Reported, not tested

Every joint and model; medians; the nominal model alone; the four GP models; C sizes and times of every joint; the
networks' formulas (logs).

## Rules

- One look: `run_robot_test.sh` runs once, start to end; its outputs are kept as they are. A failure (a crash, a
  timeout) is reported as such and not repeated with other settings.
- Nothing in the registered files changes after the fingerprint; a deviation is written to `FNET_ROBOT-deviation.md`
  before the results are read.
- The site's page (NAI-fnet) shows the result whatever it is, or is not published; the rule "publish only if NAI is on
  par with the leaders" applies, decided by the user.
