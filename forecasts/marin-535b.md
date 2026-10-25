# Prospective forecast: the final loss of the Marin 535B-A23B run

Made on 22 October 2026, while the run is still training. Its outcome is unknown to anyone
until the run ends (planned for about 1 December 2026). Status: **open**.

## The run and the target

- Marin 535B-A23B (Open Athena): a mixture-of-experts model, 18T tokens, 390,251 steps.
  Tracker: [marin-community/marin#8435](https://github.com/marin-community/marin/issues/8435);
  logs: the public W&B project `marin-community/marin_moe`.
- **Target y:** the last value of `eval_dropless/paloma/macro_loss` logged in the run's lineage
  (`hero-84579c80-072503` → … → `hero-ctx16k-step257k` → its successors) at a step of 387,000 or
  later, as W&B records it. Since step 257,553 this eval packs at 16K context
  ([#10101](https://github.com/marin-community/marin/pull/10101)); the final one is expected to as well.
- **Conditions.** If the run ends before step 387,000, or the metric's definition (its set of
  Paloma subsets) changes, the forecasts are reported and not scored. Changes made during
  training (the data mix, phase 2 from step 312,192, the planned PTB read, context switches)
  are part of the outcome and are scored.

## Forecasts

| forecast | data it saw | y | 90 % interval |
|---|---|---|---|
| **A: NAI, ladder and the run's own curve** | the ladder and the run up to step 302,999 | **1.979** | [1.965, 1.994] |
| **B: NAI, ladder only** | the four ladder rungs | **1.935** | [1.915, 1.963] |
| straight line through the run's 16K evals (my baseline) | the run's 16K evals | 1.970 | |
| Marin, 19 August 2026 ([#8435](https://github.com/marin-community/marin/issues/8435#issuecomment-5344533796)) | the ladder | 2.039 | |

Data cut: a W&B snapshot taken on 21 October 2026 at 22:58 UTC, with the run at step 302,999
(77.6 %), where the eval read 2.046.

For reference only: an independent forecast of 9 October
([#9977](https://github.com/marin-community/marin/issues/9977)) gives a median of 2.035 with an 80 %
interval of [2.023, 2.047]. Its primary target is the eval packed at 4K context, not the 16K
eval forecast here.

## How

NAI found a law of the Paloma loss L as a function of a run's compute C (without the lm_head,
Marin's own constants) and the fraction of training done. It was given no form for the law.

- **B** is that law at the run's compute and the end of training, fitted on the four rungs of
  the run's scaling ladder (rows from 30 % of training on).
- **A** adds the run's own evals at 4K context after its data swap (30 % to 65 % of training).
  The run's 16 evals at 16K context set the level: A is the law's drop from each of them to
  the end of training, averaged.
- The interval is NAI's forecast band: the forms that predict held-out rows nearly as well,
  with bootstrapped constants and a conformal widening, nominally 90 %. On SLDBench's training
  rows it covered 88 %.
- One run of NAI per table, the same build as in my other reports, no language model.

## Sealed formulas

The two laws stay sealed until the run ends. Their files are published then, and anyone can
check them against these SHA-256 digests:

| forecast | file | SHA-256 |
|---|---|---|
| A | `ladder_hero.forms` | `ebcaeac494a5fc9da20dbd6d34e678238712b07c14902f98734b4de7b4befc08` |
| B | `ladder.forms` | `af69a46e3e43f7896aabd099f4f82020bb2f4192153cbc1e99122d154c6d972b` |

The registration (data, protocol and the rules below, written before NAI was run) has the
fingerprint `48391882756bad0ec50859b281812a2f7e1b8e43667db81fd22ee80530195939`; it will be
published with the result.

## Hypotheses, fixed in advance

- **H1.** A is closer to y than Marin's 2.039.
- **H2.** y lies in A's interval.
- **H3.** A is closer to y than the straight line.
- **H4.** B is closer to y than Marin's 2.039.

## Caveats

- One outcome is one check. A hit or a miss says little about NAI's accuracy in general.
- B is a bold forecast: 0.10 below Marin's from the same ladder. Marin's law keeps a floor of
  1.5; the law NAI found keeps falling with compute, and B extrapolates it 1,900 times beyond the
  largest rung.
- The ladder was evaluated at 4K context, the final eval at 16K. B carries that difference
  unchanged; A takes the level from the run's 16K evals.

## Notes added before the outcome (25 October 2026)

These notes do not change the registration. They fix, before the outcome, how two known
effects will be handled.

- **The 4K to 16K packing offset.** A measurement in
  [#8435](https://github.com/marin-community/marin/issues/8435) (bethehand) shows that the switch
  of the eval from 4K to 16K packing alone lowered the Paloma macro by about 0.031 on nearly the
  same weights (the qk16k-a1-step252k arm: 2.0929 and 2.0926 against 2.1234 for the 4K eval of the
  same checkpoint; about 0.028 with qk_mult 1.3). Marin's 2.039 and my forecast B are both built
  on evals at 4K packing; A takes its level from the run's 16K evals. So, against the 16K target,
  the registered H1 (A against 2.039) and H4 (B against 2.039) favour my forecasts by about 0.03
  from the packing change alone; H2 and H3 are not affected. I will score H1 to H4 as registered
  and report, next to them, packing-corrected versions: the forecasts built at 4K (2.039 and B)
  against y + Δ, where Δ is the 4K minus 16K difference of the final checkpoint's evals if Marin
  logs one, and 0.0306 otherwise (0.0283 as a sensitivity check).
- **A 262K eval packing.** If the final eval packs at 262K context, the PTB and WikiText-103
  validation sets are shorter than one sequence and give no data, and the Paloma macro becomes a
  mean over 14 subsets (about +0.06). That is the registered condition "the metric's set of
  Paloma subsets changes": the forecasts are then reported and not scored. I will check it on the
  final eval itself: a loss of 0.0, or no entry, for PTB or WikiText-103 means the set changed.
  With all 16 subsets present (16K or 65K packing, or 262K with the eval's `max_seq_len` at
  65,536, [#9890](https://github.com/marin-community/marin/pull/9890)), the hypotheses are scored.
