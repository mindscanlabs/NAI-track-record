#!/bin/sh
# The fingerprint of the fifth-suite registration (docs/prereg/FNET_FIFTH.md): SHA-256 of every file it rests on, and one
# SHA-256 of that list. Run from the repository root:
#     sh docs/prereg/make_manifest_fnet_fifth.sh
set -e
out=docs/prereg/FNET_FIFTH.manifest
sha256sum \
  docs/prereg/FNET_FIFTH.md docs/prereg/make_manifest_fnet_fifth.sh \
  fnet/stand/run_fifth_test.sh fnet/stand/fifth_fetch.sh fnet/stand/fifth_checksums.py fnet/stand/fifth_prepare.py \
  fnet/stand/fifth_net.py fnet/stand/fifth_hypotheses.py \
  fnet/stand/common.py fnet/stand/prepare.py fnet/stand/niche_prepare.py fnet/stand/fresh_prepare.py \
  fnet/stand/third_prepare.py fnet/stand/baselines.py fnet/stand/nai_ref.py fnet/stand/panel_ensemble.py \
  fnet/stand/size.py fnet/stand/compare.py \
  fnet/data/fifth_assignment.tsv fnet/data/env_freeze_fifth.txt fnet/data/gcc_version.txt \
  fnet/build/v14b/nai_cli_v14b.exe fnet/build/v14b/FormulaNet_v14b.cpp fnet/build/v14b/FormulaNet_v14b.hpp \
  bench/results/v26/nai_cli_v26.exe \
  | sed 's/ \*/  /' > "$out"
cat "$out"
echo
echo "fingerprint (SHA-256 of $out):"
sha256sum "$out" | cut -d' ' -f1
