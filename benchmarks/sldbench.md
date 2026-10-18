# SLDBench: discovering neural scaling laws

*October 2026. One frozen build of NAI, five replicates.*

SLDBench (Lin et al., ICLR 2026) asks a system to discover a scaling law from training runs of neural networks and to predict the loss of larger or differently configured runs. The systems reported with the benchmark are agents built on large language models. NAI uses no language model.

## Result in brief

- **Highest mean R² among the reported systems:** 0.775 ± 0.024 over five replicates, against 0.748 for SLDAgent with GPT-5. The gap is about the spread between NAI's replicates.
- **The test was seen many times** while NAI was developed, so this is a comparison, not independent evidence.
- **Independent evidence: a check on fresh data, registered before the run.** On two new open sources NAI is far ahead of the standard Chinchilla form on one and level with it on the other, and all registered hypotheses hold.

## Ranking

| rank | system | mean R² over 8 tasks |
|---|---|---|
| **1** | **NAI** | **0.775 ± 0.024** |
| 2 | SLDAgent, GPT-5 | 0.748 |
| 3 | Goose | 0.695 |
| 4 | SLDAgent, Claude Sonnet 4.5 | 0.590 |
| 5 | CodeX | 0.550 |
| 6 | human-designed laws | 0.517 |
| 7 | SLDAgent, Gemini 2.5 Flash | 0.506 |

## Per task

| task | NAI | SLDAgent (GPT-5) | human-designed laws |
|---|---|---|---|
| parallel | 0.994 | 1.000 | 1.000 |
| vocab_size | 0.976 | 0.987 | 0.966 |
| sft | 0.983 | 0.993 | 0.957 |
| domain_mixture | 0.986 | 0.988 | 0.671 |
| moe | **0.786** | 0.773 | 0.703 |
| data_constrained | 0.904 | **0.944** | 0.911 |
| lr&bsz | 0.509 | **0.604** | -0.076 |
| u_shape | **0.063** | -0.305 | -1.000 |

NAI is ahead of SLDAgent on two tasks, within 0.02 on four, and behind on two. On u_shape every other system reported in the SLDBench paper has a negative R²; NAI's is positive in every replicate, though small (0.03 to 0.21).

## Fresh data, registered before the run

The protocol, data, baselines and binaries were fixed with a SHA-256 fingerprint before any run; I had not seen the values of the data. Baselines are standard forms from the literature, fitted on the same rows.

| data | NAI | Chinchilla form | power law in all inputs |
|---|---|---|---|
| Gemstones (22 transformers; test: the 5 largest) | **0.988** | 0.708 | 0.676 |
| Pythia (7 sizes; test: the 12B model) | **0.823** | 0.819 | -0.019 |

The registered hypotheses were: no task below 0; on at least one task, not worse than the better baseline by more than 0.02; and not worse than the earlier build by more than 0.02 on either task (the earlier build scored 0.989 and 0.382). All three hold.

An earlier check of the same kind, made with an earlier build of NAI on fresh data of five SLDBench task types, failed both of its hypotheses: NAI was better than the standard forms on two tasks (tokenization 0.986 against 0.802, data mixtures 0.989 against 0.987), worse on two, and failed catastrophically on the u_shape type, where its chosen forms exploded beyond the data. The current build was changed in response, and the change was then confirmed on the new data above before being scored on the SLDBench test. A run of the current build on the data of the earlier check will be added; it will be a run on data already seen, not a new check.

## Conditions and caveats

- **Rules.** One form per task, constants fitted per group within the benchmark's limit, the test used only for the final score, computed with SLDBench's own evaluator; five replicates, as in the SLDBench paper.
- **Budget.** About 70 minutes per search of all eight tasks on a laptop processor, so about 3.5 hours per replicate of three searches. The SLDBench repository gives 30 to 60 minutes per task for SLDAgent, which uses a large language model through an API and may have seen the papers the tasks come from.
- **Assumption given to NAI.** Loss does not increase with model size, data or the number of experts, the standard assumption of the field.
- **The test was seen 16 times** during development. The reported number comes from fifteen new searches, and the last changes were decided on other data.
- **Other systems' numbers** are from the SLDBench paper, not rerun by me.
- **Readability.** Some chosen forms are compact approximations rather than laws one would write by hand.
