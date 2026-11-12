# NAI-fnet: eight registered tests of a network of formulas for embedded models

NAI-fnet is the part of the NAI (No-Ansatz Inference) system, which I develop for finding formulas that fit given data
without fixing their form in advance, that builds a model when one formula is not enough: a network in which every
neuron is a short formula. The model is exported as plain C (no runtime, no dynamic memory), for a microcontroller or a
controller board. Its method and source code are not part of this repository; this folder records how it did in tests
whose hypotheses were written down before the one run on the test data.

Status as of 12 November 2026: eight registered tests, 32 of 40 hypotheses held. Preprint with all eight tests and
bootstrap intervals of the comparisons: Zenodo, DOI [10.5281/zenodo.24163946](https://doi.org/10.5281/zenodo.24163946).
Product page with the three device
examples and their simulators: [naiscience.com/fnet.html](https://naiscience.com/fnet.html).

| registered | test | data | hypotheses held | failed |
|---|---|---|---|---|
| 3 Nov 2026 | niche suite: 13 tables of smooth engineering and physical dependencies | open tables | 3 of 5 | H1 beyond the edge (0.520 vs tuned LightGBM 0.517), H2 reliability (4 vs 2 failures) |
| 4 Nov 2026 | fresh suite: 11 new tables, beyond the data on both sides | open tables | 4 of 5 | H2 reliability (5 vs 0 failures) |
| 5 Nov 2026 | third suite: 9 new tables | open tables | 3 of 5 | H2 reliability (7 vs 3 failures), H4 speed (0.9x of LightGBM) |
| 6 Nov 2026 | fourth suite: 7 new tables in the product's scope | open tables | 4 of 5 | H5 against an MLP beyond the edge |
| 9 Nov 2026 | [robot elbow torque](#robot-elbow-torque) | real Franka Emika Panda arm, MERL | 5 of 5 | |
| 9 Nov 2026 | [rotor temperature of a traction motor](#rotor-temperature-of-a-traction-motor) | Paderborn University test bench | 5 of 5 | |
| 9 Nov 2026 | [expected power of wind turbines](#expected-power-of-wind-turbines) | Penmanshiel wind farm | 4 of 5 | H5 energy error (IEC power curve better) |
| 10 Nov 2026 | [airliner aerodynamics](#airliner-aerodynamics) | NASA Common Research Model, wind tunnel | 4 of 5 | H3 lift beyond the measured Mach (LightGBM better) |

The four table suites: [suites.md](suites.md). The four device examples: below, with their registrations, harness
scripts and outputs in [`registered/`](registered/) and [`results/`](results/).

## What "registered" means here, and its limit

For every test, before any model was run on its test data, I wrote a registration document (the question, the data and
their split, the models, the measure, five hypotheses with their thresholds, the rules) and computed a fingerprint: the
SHA-256 of a manifest listing the SHA-256 of the registration and of every file the test rests on (the data tables, the
scripts, the program's binary). Each test then ran once, start to end; each hypothesis holds or fails as computed, with
no re-run and no deviation (none of the eight has a deviation file).

The limit: these fingerprints were kept on my own machine and were not published before the runs, so nothing outside my
records proves the time at which they were made. Publishing them now lets anyone check that the files below are the ones
the fingerprints cover; it does not prove that the registrations came first. From now on I will publish a test's
fingerprint in this repository before its run, as I did for the [Marin forecast](../forecasts/marin-535b.md).

## Robot elbow torque

*A virtual joint-torque sensor.* A robot controller needs the torque each joint motor must give (feed-forward control,
collision detection); a nominal rigid-body model of the arm misses friction, cables and errors in the nominal masses.

- **Data:** the data of "A Black-Box Physics-Informed Estimator Based on Gaussian Process Regression for Robot Inverse
  Dynamics Identification" (Giacomuzzo, Dalla Libera, University of Padua; Romeres, MERL; Zenodo 12516500, CC BY-SA 4.0),
  the real Franka Emika Panda part, with the protocol of that paper (Giacomuzzo, Carli, Romeres, Dalla Libera, IEEE
  Transactions on Robotics 40, 2024): 12
  training combinations of two trajectories each, 16 richer test trajectories, every 10th sample.
- **Formulation:** every model learns what the nominal model misses (the measured torque minus the nominal torque) from
  the joints' positions, velocities, accelerations, sin and cos of the positions (35 inputs); the nominal model ships
  with the dataset.
- **Measure:** nMSE (%) per joint, the mean over 12 combinations x 16 test trajectories, as in the paper.

| elbow (joint 4) | nMSE | C code | per prediction |
|---|---|---|---|
| **NAI-fnet** + nominal model | **0.062 %** | 33.8 KB | 0.65 µs |
| tuned LightGBM + nominal model | 0.060 % | 566 KB | 29 µs |
| MLP 32x32 + nominal model | 0.120 % | 19.0 KB | 1.2 µs |
| LIP GP, the paper's model (its published estimates) | 0.090 % | | |
| nominal model alone | 0.641 % | | |

Hypotheses: H1 fnet at most the paper's model on the elbow, **held**; H2 at most 1.25 x tuned LightGBM, **held** (LightGBM
is slightly more accurate); H3 below the MLP, **held**; H4 LightGBM's C at least 10 x larger and slower, compiled output
equal to the model's to the bit, **held** (16.7 x larger, 44.9 x slower); H5 below the paper's model on at least 5 of 7
joints, **held** (5 of 7). Reported, not tested: averaged over the seven joints the paper's model is better (3.02 % against
3.48 %), because of the wrist joint 7 (5.8 % against 11.7 %). Full output: [results/robot_test_hypotheses.txt](results/robot_test_hypotheses.txt).

## Rotor temperature of a traction motor

*A virtual temperature sensor.* The permanent magnets of a traction motor must not overheat, but a sensor on the rotating
rotor is impractical in a production drive.

- **Data:** Electric Motor Temperature (Kirchgaessner, Wallscheid, Boecker; Paderborn University; Kaggle, CC BY-SA 4.0),
  a permanent magnet synchronous motor on a test bench, 185 hours at 2 Hz. Test: profiles 60, 62 and 74, the authors'
  generalization set; the models train on the other 66 profiles.
- **Inputs:** the inverter's signals (currents, voltages, speed, coolant and ambient temperatures, derived powers) with
  moving averages, and the stator thermistors (67 inputs).
- **Measure:** MSE (K²) over all test samples, as in the authors' papers; the largest error after the first 10 minutes.

| model | MSE | largest error after 10 min | C code | per prediction |
|---|---|---|---|---|
| **NAI-fnet** | **1.76 K²** | 6.33 K | 86.8 KB | 1.1 µs |
| MLP 32x32 | 3.12 K² | 6.08 K | 27.7 KB | 2.0 µs |
| ridge regression | 5.60 K² | 7.65 K | 0.7 KB | 0.07 µs |
| tuned LightGBM | 6.62 K² | 7.77 K | 5.1 MB | 143 µs |

Hypotheses: H1 at most 1.15 x the MLP, **held**; H2 at most 0.5 x tuned LightGBM, **held**; H3 below ridge, **held**; H4
largest error after 10 minutes at most 1.25 x the MLP's, **held** (the MLP's is smaller); H5 C smaller than LightGBM's and
equal to the model to the bit, **held**. Context, not comparable (different inputs): the authors' Thermal Neural Network
on the same profiles, without the stator thermistors, reports MSE 4.34 K². Full output:
[results/motor_test_hypotheses.txt](results/motor_test_hypotheses.txt).

## Expected power of wind turbines

*The industry's reference: the turbine's power curve (IEC 61400-12-1).* The gap between produced and expected power
reveals icing, pitch or yaw faults and underperformance.

- **Data:** Penmanshiel wind farm (Cubico Sustainable Investments; Zenodo 10.5281/zenodo.16807304, CC BY 4.0), turbines
  WT11 to WT15, 10-minute SCADA; train April to December 2018, test the whole of 2019.
- **Formulation:** the IEC power curve fitted on the training rows is the nominal model; the network learns its error
  from wind speed, its standard deviation, yaw misalignment, wind direction and ambient temperature.
- **Measure:** NRMSE (RMSE / rated power 2050 kW) and the absolute energy error over the year, mean over the five turbines.

| model | NRMSE | energy error | C code (WT11) | per prediction |
|---|---|---|---|---|
| **NAI-fnet** + IEC curve | **2.26 %** | 0.40 % | 17.6 KB | 0.37 µs |
| tuned LightGBM | 2.14 % | 0.43 % | 1.1 MB | 36 µs |
| MLP 32x32 | 2.33 % | 0.34 % | 11.1 KB | 0.70 µs |
| IEC power curve | 2.95 % | 0.22 % | | |

Hypotheses: H1 below the IEC curve, **held**; H2 at most 1.15 x tuned LightGBM, **held** (LightGBM is more accurate);
H3 below the MLP, **held**; H4 LightGBM's C at least 10 x larger and slower, **held** (60.5 x, 96.7 x); H5 energy error
below the IEC curve's, **failed** (0.40 % against 0.22 %). Full output: [results/wind_test_hypotheses.txt](results/wind_test_hypotheses.txt).

## Airliner aerodynamics

*An aerodynamic model in place of a look-up table.* Flight software holds an aircraft's aerodynamic coefficients as
multi-dimensional look-up tables; beyond the measured Mach range drag rises steeply (the drag divergence).

- **Data:** NASA Common Research Model, National Transonic Facility Test 197 (2010), wall-interference corrected; a US
  Government work, NASA is acknowledged as the source and endorses nothing here. Wing-body-tail configuration; train 659
  points at Mach 0.70 to 0.85; test inside 155 points, test beyond the edge 225 points at Mach 0.86 to 0.87.
- **Inputs:** angle of attack, Mach, Reynolds number, dynamic pressure, tail incidence; one model per coefficient.
- **Measure:** RMSE per coefficient; drag in drag counts (1e-4).

| drag | beyond the measured Mach | inside | C code | per prediction |
|---|---|---|---|---|
| **NAI-fnet** | **27.8 counts** | **14.2 counts** | 20.6 KB | 2.3 µs |
| tuned LightGBM | 42.8 counts | 21.4 counts | 496 KB | 14 µs |
| MLP 32x32 | 41.9 counts | 33.3 counts | 10.8 KB | 0.67 µs |
| look-up table (interpolation, as in flight software) | 205.8 counts | 92.7 counts | 659 values | |

Hypotheses: H1 drag beyond the edge below the table, **held**; H2 at most tuned LightGBM, **held**; H3 lift beyond the
edge at most tuned LightGBM, **failed** (0.0282 against 0.0214); H4 drag inside at most 1.15 x LightGBM, **held**; H5
LightGBM's C at least 10 x larger for each coefficient, equal to the model to the bit, **held** (16.4 x, 24.1 x, 31.6 x).
Reported, not tested: pitching moment beyond the edge, NAI-fnet 0.0203 against LightGBM 0.0266. Full output:
[results/aircraft_test_hypotheses.txt](results/aircraft_test_hypotheses.txt).

## Conditions common to the four examples

- One build of NAI-fnet, released in NAI before these tests, with its released settings, 120 s, 4 threads, seed 1. None
  of the four datasets was used in its development; each formulation (inputs, target, sampling) was chosen on the
  training side only, as each registration records.
- The competitors were run by me on the same rows and inputs: LightGBM tuned by a random search over 20 settings with a
  3-fold check grouped as the data require, and an MLP with two hidden layers of 32 units and early stopping. Published
  models (the robot's GP models) enter through the authors' own estimates.
- C code size is the object file's code and constants (gcc -O2, double); time per prediction was measured on one PC for
  every model alike, not on a microcontroller. Every model's compiled C was checked against the model's own predictions.

## What is here, and what is not

[`registered/`](registered/) holds, at their paths in my repository, the four registrations, their manifests and the
manifest scripts, the harness scripts (data preparation, the runs, the hypotheses), the tables of the data files' SHA-256
and the environment's package and compiler versions. [`results/`](results/) holds the four outputs of the hypothesis
scripts as written by the registered runs.

Not published, although the manifests list them: NAI's binary and the network's source code (the method is not
disclosed), `fnet/stand/nai_ref.py` and `fnet/stand/size.py` (they hold settings of the network or its link to NAI's
formula search). The published scripts import these two files, so they document the runs but do not run as they stand.
The data are not redistributed; the scripts name their public sources, and the tables in `registered/fnet/data/` give the
SHA-256 of the prepared tables. The models' predictions are not published; a reproduction with a compiled build can be
arranged on request.

The registrations are the files exactly as fingerprinted, so they keep my machine's paths and the internal names of the
build; everything else in this folder was written afterwards.

## Checking the fingerprints

```
cd registered
sha256sum docs/prereg/FNET_ROBOT.manifest     # d016dd39c6fa38beefc0e52b4af52061603bd85b3be93b34e434b46a4a9867b4
sha256sum docs/prereg/FNET_MOTOR.manifest     # 19e310426cb7ee7cf39224220a68a60c0089d1bf2042d31e1234873033b810eb
sha256sum docs/prereg/FNET_WIND.manifest      # 0c0fa98a331c63c2d6969b9ec0802f908e94425b1a3838d039d6ff50b6dcd35c
sha256sum docs/prereg/FNET_AIRCRAFT.manifest  # 18f06eaca1a41920661a8338704402cb74a11e93bb91e9368c9aa8972db0bd4c
sha256sum -c docs/prereg/FNET_ROBOT.manifest 2>/dev/null | grep -v ': OK'   # only the withheld files are missing
```

Every published file matches its line in the manifests.

## Who did what

- **NAI** (No-Ansatz Inference), the system I develop, built the NAI-fnet models; NAI uses no language model.
- **Claude** (Anthropic), an AI assistant, wrote the test harness and drafted the registrations, ran the tests and
  drafted this summary.
- **I** chose the tests and the hypotheses, made the decisions at each step, checked the results and take
  responsibility for the content.
