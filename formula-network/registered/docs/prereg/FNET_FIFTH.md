# Registration: NAI's formula network v14b on a fifth suite of tables in its product scope (experiment 10)

Registered 2026-11-14, before any model was run on the fifth suite. The fingerprint is the SHA-256 of
`docs/prereg/FNET_FIFTH.manifest`; it is published in the NAI track record before the run. Earlier registrations of the
same experiment: the niche, fresh, third and fourth suites (2026-11-03 to 2026-11-06) and four device tests (robot,
motor, wind, aircraft, 2026-11-09 to 2026-11-10).

## Question

NAI's formula network builds a model of a table as a network whose neurons are short formulas, grown one at a time
while the next neuron pays for itself, and exports it as plain C with a range monitor. Version v14b (released in NAI as
`nai_cli --net`) follows v13, the version of the published preprint (Zenodo, DOI 10.5281/zenodo.24163946). Its changes
were aimed at reliability on noisy data and at the failures beyond the edge of the training data; v14b also adds a
graded range monitor, `fnet_range_distance`, which tells how far a point lies beyond the training ranges. On tables in
the product's scope that no part of the development has seen: is v14b as accurate as tuned gradient boosting beyond the
edge of the training data (above and below it), as reliable, not much worse inside the data, close to the best flexible
models (MLP, EBM) beyond the edge, much smaller and faster as compiled C; is it at least as good as v13; and does its
error grow with the monitor's distance, so that the monitor is informative?

## Data

The fifth suite (`fnet/stand/fifth_prepare.py`, sources fetched by `fnet/stand/fifth_fetch.sh` and checked against the
repositories' checksums by `fnet/stand/fifth_checksums.py`): 7 open tables, all of them test, never used before in this
experiment or in NAI's development:

| table | source | licence |
|---|---|---|
| ahmed_body_cd | AhmedML (Hugging Face neashton/ahmedml, DOI 10.57967/hf/5002): drag of an Ahmed body, CFD, 500 geometries | CC BY-SA 4.0 |
| lsf_wall_u | Mendeley Data 247pvf6whn v1: U-value of light-gauge steel-framed walls, COMSOL, 5 000 designs | CC BY 4.0 |
| composite_curing_distortion | Zenodo 19450971: curing distortion of flat composite panels, FE, 6 000 cases | CC BY 4.0 |
| cellular_beam_wu | Mendeley Data zcm29bp7yf v2: ultimate load of cellular steel beams, FE, 81 sections | CC BY 4.0 |
| hts_wire_ic | figshare 3759315: critical current of a SuperOx GdBCO HTS wire, laboratory | CC BY 4.0 |
| zr_hydrogen_tss | Zenodo 23954638 v1: terminal solid solubility of hydrogen in zirconium alloys, compilation of 59 publications | CC BY 4.0 |
| lpbf_density | Zenodo 6514897 v1.1: laser powder bed fusion parameters and relative density, compilation of 164 papers | CC BY 4.0 |

**Selection.** A search excluded every table used or considered before (the general suite, the niche, fresh, third and
fourth suites, their candidate lists and the device data) and returned 13 candidates and 5 spares. The tables were
chosen by the product's scope with the criteria of the fourth suite, applied to the sources' descriptions and column
names before any model was run: the target is a physical quantity that depends on a few quantities; the use is one of
the product's (a surrogate, an embedded model, a calibration); the inputs are mostly numeric physical quantities, not
category codes; laboratory data or simulation; about 30 independent objects or more. Not taken by these criteria:
pressure on H-shaped buildings and gas solubility in brines (category codes dominate), gyrokinetic growth rates (17
inputs and mode classes, outside the product's uses), the air gap of electric machines (ambiguous input columns, number
of geometries unknown), membrane distillation (20 geometries), multiaxial fatigue (censored run-outs, 12 materials).
Because reliability on noisy data is the main aim of v14, the two noisy compilations among the candidates (hydrogen in
zirconium, LPBF) were taken. The HTS wire is the item of a 24-wire collection that the search opened first, not chosen
by its values. These decisions were made without the user's review, under the user's instruction to work autonomously
up to this registration.

**What was seen before registration.** No model was run on these tables. The candidate search and the preparation
opened headers, sheet names, row counts and group counts; in doing so one data row each of the LSF wall and HTS wire
files was printed (one target value of the wall, none of the wire); the search opened the candidates' file headers,
which may have shown their first rows. No relation between inputs and targets was examined.

Which columns are inputs, the targets, the cleaning and the splits were fixed in `fifth_prepare.py` from the sources'
descriptions and column names. Not inputs: other outputs of the same system, columns derived from the target or computed
from other inputs, identifiers, sources, authors, apparatus, measurement metadata and uncertainties, other models'
predictions and fits (listed per table in the code). The general cleaning rules (the same as in all earlier suites) drop
categorical columns with more than 10 levels and columns with more than 20 % missing values; here they removed the
alloying contents of the zirconium table (the solvus temperature and the solvus type remain) and the material and the
sparse process parameters of the LPBF table. Tables, splits and their SHA-256: `fnet/data/fifth_assignment.tsv`.

Splits (`fnet/stand/prepare.py`, as in the earlier suites): **iid1** (75/25 by groups, seed 1: a beam section, an angle
sweep of the wire (set temperature and field), a measurement run, a paper and material; in the other tables rows with
identical inputs form a group); **xfeat** (train at or below the 80 % quantile of the input with the largest |Spearman
rho| with the target among inputs with at least 20 distinct values, test above; test share 10-30 %); **xy** (the same by
the target); **xfeat_lo** and **xy_lo** (the mirror). Every table has all five splits: 35 (table, split) pairs, 7 inside
and 28 edge.

## Models (one run each; `fnet/stand/run_fifth_test.sh`)

- **fnet v14b**: `nai_cli --net` of `fnet/build/v14b/nai_cli_v14b.exe` (NAI's development build with network v14b; the
  network's code is `fnet/build/v14b/FormulaNet_v14b.cpp`), released settings, no other flag; 120 s, 4 threads, seed 1
  (`fnet/stand/fifth_net.py`).
- **fnet v13**: `nai_cli --net` of NAI v26 (`bench/results/v26/nai_cli_v26.exe`, network v13), the same way.
- **Tuned boosting**: LightGBM and CatBoost, random search over 20 settings, 3-fold check inside the training rows
  (`baselines.py`, `lightgbm_tuned`, `catboost_tuned`).
- **Other models**: LightGBM, XGBoost, CatBoost (defaults), EBM, FFX, MLP, ridge, the training mean and the edge constant
  (`baselines.py`).
- **Compiled size and speed**: `fifth_net.py --size` (as `size.py` measures them): v14b's `--export-c` against default
  LightGBM through m2cgen, both `gcc -O2`, double; one split per table (iid1).

## Measure

Relative RMSE = RMSE on the test rows / RMSE of the training mean on them, per (table, split). Non-finite predictions are
replaced by the training mean (`common.metrics`) and counted. **Inside** = the pairs with split iid1; **edge** = the pairs
with split xfeat, xy, xfeat_lo or xy_lo. A model's value for a group is the median over the group's (table, split)
pairs. Computed by `fnet/stand/fifth_hypotheses.py --side test --net fnet_v14b --old fnet_v13`.

## Hypotheses

H1-H5 as for the fresh, third and fourth suites; H6 and H7 are new.

- **H1 (beyond the edge, both tails):** the edge median of v14b is at most that of tuned LightGBM.
- **H2 (reliability):** the number of (table, split) pairs where v14b is worse than the training mean (relative RMSE
  above 1) is not larger than tuned LightGBM's.
- **H3 (inside the data):** the inside median of v14b is at most 1.5 x that of tuned LightGBM.
- **H4 (compiled C):** over the test tables, the median of (LightGBM size / network size) is at least 10 and the median
  of (LightGBM time / network time per prediction) is at least 3.
- **H5 (against the best flexible models, beyond the edge):** the edge median of v14b is at most 1.15 x that of MLP and
  at most 1.15 x that of EBM.
- **H6 (v14b against v13):** over all 35 pairs, the geometric mean of (v14b's relative RMSE / v13's) is at most 1.02,
  and v14b has no more pairs above 1 than v13.
- **H7 (the graded range monitor):** among the edge pairs with at least 10 test points at a distance of at most 0.1
  and at least 10 beyond 0.25 (the distance of `fnet_range_distance`: the largest, over the inputs, of the distance
  outside the input's training range in units of that range), v14b's RMSE on the far points exceeds its RMSE on the
  near points in at least two thirds of the pairs; at least 5 such pairs are needed, otherwise H7 fails.

Each hypothesis holds or fails as computed; no correction, no re-run. Expectations from the development material (224
pairs of the niche, fresh, third and fourth suites with every model; v14 was chosen on them, so they are optimistic):
edge median 0.427 for v14 against 0.492 for tuned LightGBM, 0.465 for MLP and 0.470 for EBM; inside 0.298 against
0.238 (1.25 x); 10 pairs above 1 for v14, v13 and tuned LightGBM alike; v14 against v13, geometric mean 0.996; far
error above near error in 51 of 56 eligible edge pairs (91 %). For H4: on the fourth suite v11's C code was 46 x
smaller and 3.9 x faster than LightGBM (medians over 7 tables); in a dry run of this harness on one development table
(droplet_spreading, iid1) v14b's code was 37 x smaller and 0.93 x as fast (v11 on the same table: 46 x and 1.1 x), so
the speed part of H4 may fail. With 7 tables, H4's medians rest on few values.

## Reported, not tested

Per table and split: every model's relative RMSE, the upper and lower tails separately, the edge constant, default
boosting, FFX; non-finite predictions; worst cases; sizes and times per table; v13's values; the near and far errors
of H7 per pair.

## Rules

- One look: `run_fifth_test.sh` runs once, start to end; its outputs are kept as they are. A failure of a run (a crash,
  a timeout) is reported as such and not repeated with other settings.
- Nothing in the registered files changes after the fingerprint; a deviation is written to `FNET_FIFTH-deviation.md`
  before the results are read.
- The general suite's test part (28 tables, `fnet/data/assignment.tsv`) stays closed.
- What follows from the result (publication) is decided afterwards by the user; the rule "publish only if NAI is on par
  with the leaders" applies.
