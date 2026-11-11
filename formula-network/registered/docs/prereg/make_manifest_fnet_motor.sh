#!/bin/sh
# The fingerprint of the motor registration (docs/prereg/FNET_MOTOR.md). Run from the repository root:
#     sh docs/prereg/make_manifest_fnet_motor.sh
set -e
out=docs/prereg/FNET_MOTOR.manifest
sha256sum \
  docs/prereg/FNET_MOTOR.md docs/prereg/make_manifest_fnet_motor.sh \
  fnet/stand/run_motor_test.sh fnet/stand/motor_prepare.py fnet/stand/motor_run.py fnet/stand/motor_hypotheses.py \
  fnet/stand/robot_run.py fnet/stand/common.py fnet/stand/competitors.py fnet/stand/nai_ref.py fnet/stand/size.py \
  fnet/data/motor_tables.tsv fnet/data/env_freeze_competitors.txt fnet/data/gcc_version.txt \
  bench/results/v26/nai_cli_v26.exe src/Net/FormulaNet.cpp src/Net/FormulaNet.hpp \
  | sed 's/ \*/  /' > "$out"
cat "$out"
echo
echo "fingerprint (SHA-256 of $out):"
sha256sum "$out" | cut -d' ' -f1
