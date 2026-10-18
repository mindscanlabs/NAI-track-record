# Benchmarks

Short reports of NAI on public benchmarks, with the other systems where a comparison exists. Every number is from one frozen build of NAI, except where marked, run on a laptop processor without a GPU or a language model.

| benchmark | task | NAI | best other system | report |
|---|---|---|---|---|
| SRBench 2021 | exact recovery of the Feynman equations, no noise | **60.3 %, 1st** | AI Feynman 55.8 % | [srbench](srbench.md) |
| SRBench 2021 | Feynman equations, 1 % noise | **48.3 %, 1st** | gplearn 13.2 % | [srbench](srbench.md) |
| SRBench 2021 | ODE-Strogatz systems | **85.7 %, 1st** | GP-GOMEA 29.5 % | [srbench](srbench.md) |
| SRBench 2025 | real measurements of physical laws, median R² | **0.9925, 1st of 28** | QLattice 0.987 | [srbench](srbench.md) |
| SRBench 2025 | black-box regression, mean R² | 0.090, 26th of 29 | Rils-Rols 0.640 | [srbench](srbench.md) |
| SLDBench | discovering neural scaling laws, mean R² | **0.775, 1st** | SLDAgent (GPT-5) 0.748 | [sldbench](sldbench.md) |
| OEIS | sequences with a known formula | 136 of 140, none wrong | no shared benchmark | [oeis](oeis.md) |

Checks registered before the run, on data I had not used:

| check | NAI | reference |
|---|---|---|
| NIST StRD, 15 datasets of real measurements, median R² | 0.9887 | certified models (know the form) 0.9937 |
| Gemstones scaling data, R² | 0.988 | Chinchilla form 0.708 |
| Pythia scaling data, R² | 0.823 | Chinchilla form 0.819 |
| fresh data of five SLDBench task types (earlier build) | 2 of 5 tasks at or above the standard forms | hypotheses not confirmed |

Each report states the conditions and what was seen during development.
