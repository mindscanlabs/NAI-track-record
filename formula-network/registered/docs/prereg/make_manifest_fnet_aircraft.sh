#!/bin/sh
# The fingerprint of the aircraft registration (docs/prereg/FNET_AIRCRAFT.md). Run from the repository root:
#     sh docs/prereg/make_manifest_fnet_aircraft.sh
set -e
out=docs/prereg/FNET_AIRCRAFT.manifest
sha256sum \
  docs/prereg/FNET_AIRCRAFT.md docs/prereg/make_manifest_fnet_aircraft.sh \
  fnet/stand/run_aircraft_test.sh fnet/stand/aircraft_prepare.py fnet/stand/aircraft_run.py fnet/stand/aircraft_hypotheses.py \
  fnet/stand/robot_run.py fnet/stand/common.py fnet/stand/competitors.py fnet/stand/nai_ref.py fnet/stand/size.py \
  fnet/data/aircraft_tables.tsv fnet/data/env_freeze_competitors.txt fnet/data/gcc_version.txt \
  bench/results/v26/nai_cli_v26.exe src/Net/FormulaNet.cpp src/Net/FormulaNet.hpp \
  | sed 's/ \*/  /' > "$out"
cat "$out"
echo
echo "fingerprint (SHA-256 of $out):"
sha256sum "$out" | cut -d' ' -f1
