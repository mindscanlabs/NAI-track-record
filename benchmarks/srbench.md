# SRBench: recovering known laws

*October 2026. One frozen build of NAI, one run per problem.*

SRBench (La Cava et al. 2021; 2025 update by Aldeia et al.) is the standard benchmark for symbolic regression. It has two kinds of problems: ground-truth problems, where the generating formula is known and the question is whether a method recovers it, and problems where only the accuracy of the prediction can be measured.

## Result in brief

- **Exact recovery of known laws (2021 suite): first in every task.** 70 of the 116 Feynman equations without noise, 56 with 1 % noise, 12 of the 14 ODE-Strogatz problems.
- **Real measurements of physical laws (2025 suite): first of 28 by median R².** First or level with the best on 6 of the 13 problems.
- **Black-box regression (2025 suite): 26th of 29.** NAI looks for laws; where there is none, it returns a short approximation and is not competitive.
- **Pre-registered check on new measurements (NIST): within 0.01 of the certified models** that are given the form of the law, with a numeric prediction on every dataset.

## Exact recovery, SRBench 2021

A solution is a formula that differs from the true one by a constant term or factor, checked with sympy as in SRBench. Percent of problems; other methods: mean over their 10 runs, from SRBench's published table.

| method | Feynman, no noise (116) | Feynman, 1 % noise | ODE-Strogatz (14) |
|---|---|---|---|
| **NAI** | **60.3** (strict check 56.9) | **48.3** (strict check 45.7) | **85.7** |
| AI Feynman | 55.8 * | 0.0 | 27.1 |
| AFP_FE | 27.0 | 6.1 | 20.0 |
| GP-GOMEA | 26.8 | 0.0 | 29.5 |
| ITEA | 22.4 | 0.1 | 7.1 |
| AFP | 21.1 | 7.1 | 15.2 |
| DSR | 19.7 | 8.4 | 19.6 |
| gplearn | 16.3 | 13.2 | 8.9 |

\* over 114 of the 116 equations.

"Strict check": sympy with plain symbols. The main numbers declare the variables positive, as every Feynman variable is; four correct solutions without noise (three with noise) are identities that only hold for positive values, such as sqrt(a)/sqrt(b) = sqrt(a/b). NAI is first under both checks.

**Feynman equations, no noise** (% recovered exactly):

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/feynman_dark.svg">
  <img src="charts/feynman_light.svg" alt="Feynman equations recovered without noise: NAI 60.3 %, AI Feynman 55.8 %, AFP_FE 27.0 %, and others">
</picture>

**Feynman equations, 1 % noise:**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/feynman_noise_dark.svg">
  <img src="charts/feynman_noise_light.svg" alt="Feynman equations recovered with 1 % noise: NAI 48.3 %, gplearn 13.2 %, EPLEX 8.8 %, and others">
</picture>

**ODE-Strogatz systems:**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/strogatz_dark.svg">
  <img src="charts/strogatz_light.svg" alt="ODE-Strogatz problems recovered: NAI 85.7 %, GP-GOMEA 29.5 %, AI Feynman 27.1 %, and others">
</picture>

On accuracy (R² > 0.999 on the test set, Feynman without noise) NAI reaches 71.6 %, level with GP-GOMEA and behind MRGP (93.1 %), Operon (86.2 %), AI Feynman (78.5 %) and SBP-GP (73.7 %).

## Real measurements, SRBench 2025

Thirteen datasets of real measurements of known laws (Hubble, Kepler, Planck, Rydberg, Newton and others). Per method, the median over its runs on each dataset, then over the datasets. By median R² NAI is first; by mean R² it is fourth.

| method | median R² | mean R² (below -1 counted as -1) |
|---|---|---|
| **NAI** | **0.9925** | 0.803 |
| QLattice | 0.987 | 0.839 |
| PySR | 0.914 | 0.815 |
| Operon | 0.913 | 0.839 |
| Rils-Rols | 0.901 | 0.788 |
| Bingo | 0.894 | 0.710 |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/first_principles_dark.svg">
  <img src="charts/first_principles_light.svg" alt="SRBench 2025 first-principles median R²: NAI 0.9925, QLattice 0.9867, PySR 0.9135, and others">
</picture>

The chart shows the top 12 of the 28 systems by median R².

NAI is first or level with the best on Newton, Bode, Schechter, Planck, a supernova set and Rydberg. Its mean is pulled down by Hubble (8 test rows), Leavitt and Kepler, where its approximations do not extrapolate.

On the 12 black-box datasets NAI's mean R² is 0.090 (best: Rils-Rols 0.640), 26th of 29:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/black_box_dark.svg">
  <img src="charts/black_box_light.svg" alt="SRBench 2025 black-box mean R²: Rils-Rols 0.640 first; NAI 0.090, 26th of 29">
</picture>


## New measurements, registered before the run

Fifteen nonlinear regression datasets of real measurements from the NIST Statistical Reference Datasets, which I had not used before. The protocol and data were fixed with a SHA-256 fingerprint before any run. The reference is NIST's certified model, which knows the form of the law; NAI does not.

| | NAI | certified model |
|---|---|---|
| median R² | 0.9887 | 0.9937 |
| mean R² | 0.738 | 0.859 |
| datasets without a numeric prediction | 0 | 0 |

NAI is within 0.01 of the certified model or better on 12 of the 15 datasets, and far better on Nelson (0.906 against 0.117). It is clearly worse on three: Rat42 (0.938 against 0.994), ENSO (-0.67 against 0.39, a series with three periods) and BoxBOD (-21.9 against 0.50, 6 rows), which pull its mean down.

## Conditions and caveats

- **Budget.** NAI: one run, 120 seconds, 400 training rows (Feynman), on a laptop processor. Other methods: up to 8 hours, 10,000 rows and 10 runs (2021); one hour, tuning and 30 runs (2025). NAI's variance over runs is therefore not measured.
- **Not the same rows.** The Feynman data were regenerated from PMLB's metadata, as SRBench generated them, and the 2025 comparison uses NAI's own 75 / 25 split; on small datasets R² depends on the split.
- **Not blind.** These suites are public, and some development decisions were made with their logs in view. The NIST check is the blind one.
- **The 2021 table is old.** The 2025 update published no exact-recovery table for current methods.
- **Readability.** On real measurements NAI's answers are accurate approximations, not always the textbook law.
