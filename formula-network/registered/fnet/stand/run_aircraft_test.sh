#!/bin/sh
# The registered single run on the aircraft's test points (docs/prereg/FNET_AIRCRAFT.md). One job at a time.
#     sh fnet/stand/run_aircraft_test.sh
set -e
PY=/d/Claude/fnet-env/Scripts/python.exe
REG=C:/msys64/home/ceo/nai/docs/prereg/FNET_AIRCRAFT.md
L=/d/Claude/nai-data/fnet/aircraft
cd /c/msys64/home/ceo/nai/fnet/stand
$PY -s -E aircraft_run.py --side test --registered $REG --models fnet,table,lightgbm_tuned,mlp32 > $L/test_run.log 2>&1
$PY -s -E aircraft_hypotheses.py --results D:/Claude/nai-data/fnet/results/aircraft_test > $L/test_hypotheses.txt 2>&1
echo done
