# LLM-SRBench: new equations, unseen before the run

*October 2026. One frozen build of NAI, one run per problem, registered in advance. A second
registered run with a newer build is reported [below](#second-run-a-newer-build-a-second-look),
as a second look at the same test.*

LLM-SRBench (Shojaee et al., ICML 2025) was built to test equation discovery by systems based on
large language models. Its problems are chosen so that a model cannot simply recall the answer:

- **LSR-Transform** (111 problems): Feynman's equations rewritten for another variable, with
  roots and solved equations in them; 2 to 8 inputs.
- **LSR-Synth** (129 problems): known laws of chemistry, biology, physics and materials science
  with synthetic terms added; 2 to 3 inputs, a held-out range for extrapolation.

NAI had not been run on these data before. The run, its metrics and its hypotheses were
registered before it started.

## Result in brief

- **First by accuracy in three of the five sets:** chemistry (80.56 %), biology (75.00 %) and
  physics (43.18 %), ahead of all twelve LLM-based systems of the paper.
- **Fourth in the other two:** LSR-Transform (45.05 %, behind three LaSR variants, best 50.45 %)
  and materials science (80.00 %, behind three LLM-SR variants, best 88.28 %).
- **Recovering the exact law is NAI's weak side here.** On LSR-Transform 18.02 % of NAI's formulas
  are symbolically identical to the true law under a strict check; the best system of the paper
  reaches 31.53 % on a softer, model-judged measure.
- NAI uses no language model and gets no description of the variables, only the table.
- **Second run** (a newer build, units of the variables and the float32 precision of the data
  in the tables, the same test): first in four sets of five, LSR-Transform included (72.07 %),
  third in materials science (84.00 %); 35 of the 111 LSR-Transform laws recovered exactly under
  the strict check. It is a second look at the test, so the first run stays the main result.

## Conditions

- **NAI:** one frozen build, the same settings for every problem, one run per problem; 300 s per
  problem on a laptop processor (6 threads); at most 2 000 training rows, a random sample; the
  test and the out-of-range sets in full.
- **Other systems:** the numbers published in the paper's main table: Direct prompting, SGA, LaSR
  and LLM-SR, each with Llama-3.1-8B, GPT-3.5-turbo and GPT-4o-mini.
- **Accuracy (Acc0.1):** the share of problems where the formula is within 10 % of the true value
  on every test point, as in the benchmark's own pipeline.

## Accuracy, Acc0.1 (%)

| set | problems | NAI | best other system | NAI's place of 13 |
|---|---|---|---|---|
| LSR-Transform | 111 | 45.05 | 50.45 (LaSR, GPT-4o-mini) | 4th |
| LSR-Synth: chemistry | 36 | **80.56** | 66.66 (LLM-SR, Llama-3.1-8B) | **1st** |
| LSR-Synth: biology | 24 | **75.00** | 58.33 (LLM-SR, Llama-3.1-8B) | **1st** |
| LSR-Synth: physics | 44 | **43.18** | 36.36 (LLM-SR, GPT-4o-mini) | **1st** |
| LSR-Synth: materials science | 25 | 80.00 | 88.28 (LLM-SR, GPT-4o-mini) | 4th |

**LSR-Transform:**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/llmsr_transform_dark.svg">
  <img src="charts/llmsr_transform_light.svg" alt="LSR-Transform Acc0.1: NAI, second run 72.07 %, LaSR (GPT-4o-mini) 50.45 %, LaSR (GPT-3.5-turbo) 47.74 %, LaSR (Llama-3.1-8B) 45.94 %, NAI 45.05 %, LLM-SR (GPT-4o-mini) 39.64 %, and others">
</picture>

**LSR-Synth, chemistry:**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/llmsr_chem_dark.svg">
  <img src="charts/llmsr_chem_light.svg" alt="LSR-Synth chemistry Acc0.1: NAI, second run 91.67 %, NAI 80.56 %, LLM-SR (Llama-3.1-8B) 66.66 %, LLM-SR (GPT-4o-mini) 52.77 %, and others">
</picture>

**LSR-Synth, biology:**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/llmsr_bio_dark.svg">
  <img src="charts/llmsr_bio_light.svg" alt="LSR-Synth biology Acc0.1: NAI 75.00 %, NAI, second run 70.83 %, LLM-SR (Llama-3.1-8B) 58.33 %, LLM-SR (GPT-4o-mini) 29.16 %, and others">
</picture>

**LSR-Synth, physics:**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/llmsr_phys_dark.svg">
  <img src="charts/llmsr_phys_light.svg" alt="LSR-Synth physics Acc0.1: NAI, second run 47.73 %, NAI 43.18 %, LLM-SR (GPT-4o-mini) 36.36 %, LLM-SR (Llama-3.1-8B) 34.09 %, and others">
</picture>

**LSR-Synth, materials science:**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/llmsr_matsci_dark.svg">
  <img src="charts/llmsr_matsci_light.svg" alt="LSR-Synth materials science Acc0.1: LLM-SR (GPT-4o-mini) 88.28 %, LLM-SR (Llama-3.1-8B) 88.12 %, NAI, second run 84.00 %, LLM-SR (GPT-3.5-turbo) 82.14 %, NAI 80.00 %, and others">
</picture>

## Recovering the law itself

The paper measures symbolic accuracy with GPT-4o, which compares the forms of the two equations
without their constants. I used a strict check instead: the difference or the ratio of NAI's
formula and the true one must simplify to a constant in sympy, as in SRBench.

| set | NAI, strict check | best of the paper, model-judged |
|---|---|---|
| LSR-Transform | 18.02 % (20 of 111) | 31.53 % (LLM-SR, GPT-4o-mini) |
| LSR-Synth: biology and materials science | 0 of 49 | 25.30 % and 28.12 % |

The measures differ, but the strict one is not the softer of the two, and on LSR-Transform NAI
recovers fewer laws. On LSR-Synth the true laws contain synthetic terms; NAI finds formulas of
another form that fit the data almost exactly (normalised error below 10⁻¹⁰ on 60 of the 129
problems) and are not the reference form. The same holds on LSR-Transform for 37 of the 111.

## Second run: a newer build, a second look

*Registered on 20 October 2026, before the run; one run per problem, the same protocol.*

The first run left a clear trace: on 19 LSR-Transform problems NAI found an almost exact formula,
but its constants stayed real numbers instead of the true simple ones. The benchmark stores its
data as float32 (about 7 digits), and the tables gave NAI no way to know that the last digits
were rounding. Two things changed after it:

- **The tables** now carry what the data are: the standard units of the variables on
  LSR-Transform (Feynman's equations; the systems of the paper get descriptions of the variables
  in their prompts), and a column with the precision of float32 on every set.
- **The build:** a newer frozen build of NAI that treats a precision this fine as the precision
  of the record, not as noise. The rest of the search is the same for every table.

Because these changes came from studying the first run's outputs, the second run measures what
they bring on the same test; it is not an independent check. All three registered hypotheses
held.

| set | first run | second run | best other system | place of 13 |
|---|---|---|---|---|
| LSR-Transform | 45.05 % | **72.07 %** | 50.45 % (LaSR, GPT-4o-mini) | **1st** |
| LSR-Synth: chemistry | 80.56 % | **91.67 %** | 66.66 % (LLM-SR, Llama-3.1-8B) | **1st** |
| LSR-Synth: biology | 75.00 % | **70.83 %** | 58.33 % (LLM-SR, Llama-3.1-8B) | **1st** |
| LSR-Synth: physics | 43.18 % | **47.73 %** | 36.36 % (LLM-SR, GPT-4o-mini) | **1st** |
| LSR-Synth: materials science | 80.00 % | 84.00 % | 88.28 % (LLM-SR, GPT-4o-mini) | 3rd |

The place counts the second run against the twelve systems of the paper. The charts above show
both runs.

**Recovering the law.** On LSR-Transform the strict check now accepts 35 of 111 formulas
(31.53 %), against 20 in the first run; the best system of the paper reaches the same 31.53 % on
its softer, model-judged measure. NAI now declares 45 of the 111 problems solved exactly and 8
more fitted to within the noise, against 1 and 0 in the first run. On LSR-Synth biology and
materials science the strict check still accepts none.

**What got worse:** 2 LSR-Transform problems and 3 strict matches lost against the first run,
and biology fell from 75.00 % to 70.83 % (one problem gained, two lost); the registration allowed
a fall of up to 5 points there.

## Notes on the run

- **Two corrections to the harness, both recorded before scoring:**
  - in materials science the quantity to explain is called `sigma`, which NAI reads as the
    column of standard errors; the column was renamed and the 25 problems were run again with the
    same build and settings;
  - the symbolic check is limited to 60 s per formula, as in SRBench.
- **An error in my registration.** It named LLM-SR (39.64 %) as the best system of the paper on
  LSR-Transform. The paper's table has three LaSR variants above it, up to 50.45 %. This page
  compares with the full table; against it NAI is fourth on LSR-Transform, not first.
- **Normalised errors** (NMSE) are not compared here: I have not checked how the paper aggregates
  them over the problems.

## Reproduction

NAI's outputs on these problems are not published. A compiled build of NAI that runs these
problems, or any other table, is available on request: lab@mindscan.org.

Benchmark: Shojaee, P., Nguyen, N.-H., Meidani, K., Farimani, A. B., Doan, K. D., Reddy, C. K.
*LLM-SRBench: A New Benchmark for Scientific Equation Discovery with Large Language Models.*
ICML 2025. arXiv:2504.10415.
