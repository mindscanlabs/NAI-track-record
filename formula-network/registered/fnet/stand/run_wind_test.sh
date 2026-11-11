#!/bin/sh
# The registered single run on the wind test year (docs/prereg/FNET_WIND.md). One job at a time.
#     sh fnet/stand/run_wind_test.sh
set -e
PY=/d/Claude/fnet-env/Scripts/python.exe
REG=C:/msys64/home/ceo/nai/docs/prereg/FNET_WIND.md
L=/d/Claude/nai-data/fnet/wind
cd /c/msys64/home/ceo/nai/fnet/stand
$PY -s -E wind_run.py --side test --registered $REG --step 2 --models fnet_res,iec,lightgbm_tuned,mlp32 > $L/test_run.log 2>&1
$PY -s -E wind_hypotheses.py --results D:/Claude/nai-data/fnet/results/wind_test > $L/test_hypotheses.txt 2>&1
echo done
