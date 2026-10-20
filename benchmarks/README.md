# Benchmarks

Short reports of NAI on public benchmarks, with the other systems where a comparison exists. Every number is from one frozen build of NAI, except where marked, run on a laptop processor without a GPU or a language model.

| benchmark | task | NAI | best other system | report |
|---|---|---|---|---|
| SRBench 2021 | exact recovery of the Feynman equations, no noise | **60.3 %, 1st** | AI Feynman 55.8 % | [srbench](srbench.md) |
| SRBench 2021 | Feynman equations, 1 % noise | **48.3 %, 1st** | gplearn 13.2 % | [srbench](srbench.md) |
| SRBench 2021 | ODE-Strogatz systems | **85.7 %, 1st** | GP-GOMEA 29.5 % | [srbench](srbench.md) |
| SRBench 2025 | real measurements of physical laws, median R² | **0.9925, 1st of 28** | QLattice 0.987 | [srbench](srbench.md) |
| SRBench 2025 | black-box regression, mean R² | 0.090, 26th of 29 | Rils-Rols 0.640 | [srbench](srbench.md) |
| SLDBench | discovering neural scaling laws, mean R² | **0.775 ± 0.024, 1st** (within the spread of replicates) | SLDAgent (GPT-5) 0.748 | [sldbench](sldbench.md) |
| LLM-SRBench | new equations, LSR-Synth chemistry / biology / physics, Acc0.1 | **80.56 / 75.00 / 43.18 %, 1st** in each | LLM-SR 66.66 / 58.33 / 36.36 % | [llmsrbench](llmsrbench.md) |
| LLM-SRBench | LSR-Synth materials science, Acc0.1 | 80.00 %, 4th of 13 | LLM-SR (GPT-4o-mini) 88.28 % | [llmsrbench](llmsrbench.md) |
| LLM-SRBench | LSR-Transform, Acc0.1 | 45.05 %, 4th of 13 | LaSR (GPT-4o-mini) 50.45 % | [llmsrbench](llmsrbench.md) |
| LLM-SRBench, second run (second look) | LSR-Transform / chemistry / biology / physics, Acc0.1 | **72.07 / 91.67 / 70.83 / 47.73 %, 1st** in each | LaSR 50.45; LLM-SR 66.66 / 58.33 / 36.36 % | [llmsrbench](llmsrbench.md#second-run-a-newer-build-a-second-look) |
| LLM-SRBench, second run (second look) | LSR-Synth materials science, Acc0.1 | 84.00 %, 3rd of 13 | LLM-SR (GPT-4o-mini) 88.28 % | [llmsrbench](llmsrbench.md#second-run-a-newer-build-a-second-look) |
| OEIS | sequences with a known formula | 136 of 140, none wrong | no shared benchmark | [oeis](oeis.md) |

Checks registered before the run, on data I had not used:

| check | NAI | reference |
|---|---|---|
| NIST StRD, 15 datasets of real measurements, median R² | 0.9887 | certified models (know the form) 0.9937 |
| Gemstones scaling data, R² | 0.988 | Chinchilla form 0.708 |
| Pythia scaling data, R² | 0.823 | Chinchilla form 0.819 |
| fresh data of five SLDBench task types (earlier build) | 2 of 5 tasks at or above the standard forms; a failure on u_shape | hypotheses not confirmed |

Each report states the conditions and what was seen during development.

**Reproduction.** The 40 SLDBench solutions (5 runs of 8 tasks, each a self-contained program scored by SLDBench's own evaluator) are submitted to the benchmark's public results dataset: [pull request](https://huggingface.co/datasets/pkuHaowei/scaling_law_discovery_results/discussions/2). NAI's other outputs (chosen formulas and logs of the other runs) are not published; a compiled build of NAI that reproduces these results on the benchmarks' data, and runs on any other data, is available on request: lab@mindscan.org.
