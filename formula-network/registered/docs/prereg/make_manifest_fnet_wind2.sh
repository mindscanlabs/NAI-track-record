#!/bin/sh
# The fingerprint of the second wind registration (docs/prereg/FNET_WIND2.md): SHA-256 of every file it rests on, and
# one SHA-256 of that list. Run from the repository root:
#     sh docs/prereg/make_manifest_fnet_wind2.sh
set -e
out=docs/prereg/FNET_WIND2.manifest
sha256sum \
  docs/prereg/FNET_WIND2.md docs/prereg/make_manifest_fnet_wind2.sh \
  fnet/stand/run_wind2_test.sh fnet/stand/wind2_prepare.py fnet/stand/wind2_run.py fnet/stand/wind2_hypotheses.py \
  fnet/stand/common.py fnet/stand/nai_ref.py fnet/stand/robot_run.py fnet/stand/competitors.py fnet/stand/size.py \
  fnet/data/wind2_tables.tsv fnet/data/env_freeze_fifth.txt fnet/data/gcc_version.txt \
  fnet/build/v14b/nai_cli_v14b.exe fnet/build/v14b/FormulaNet_v14b.cpp fnet/build/v14b/FormulaNet_v14b.hpp \
  | sed 's/ \*/  /' > "$out"
cat "$out"
echo
echo "fingerprint (SHA-256 of $out):"
sha256sum "$out" | cut -d' ' -f1
