#!/bin/sh
# The fingerprint of the robot registration (docs/prereg/FNET_ROBOT.md): SHA-256 of every file it rests on, and one
# SHA-256 of that list. Run from the repository root:
#     sh docs/prereg/make_manifest_fnet_robot.sh
set -e
out=docs/prereg/FNET_ROBOT.manifest
sha256sum \
  docs/prereg/FNET_ROBOT.md docs/prereg/make_manifest_fnet_robot.sh \
  fnet/stand/run_robot_test.sh fnet/stand/robot_prepare.py fnet/stand/robot_nominal.py fnet/stand/robot_run.py \
  fnet/stand/robot_hypotheses.py fnet/stand/robot_baselines.py fnet/stand/run_robot_dev.sh fnet/stand/run_robot_dev2.sh \
  fnet/stand/common.py fnet/stand/baselines.py fnet/stand/competitors.py fnet/stand/nai_ref.py fnet/stand/size.py \
  fnet/data/robot_tables.tsv fnet/data/robot_estimates_index.tsv fnet/data/env_freeze_competitors.txt \
  fnet/data/gcc_version.txt bench/results/v26/nai_cli_v26.exe src/Net/FormulaNet.cpp src/Net/FormulaNet.hpp \
  | sed 's/ \*/  /' > "$out"
cat "$out"
echo
echo "fingerprint (SHA-256 of $out):"
sha256sum "$out" | cut -d' ' -f1
