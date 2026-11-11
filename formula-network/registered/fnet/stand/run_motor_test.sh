#!/bin/sh
# The registered single run on the motor's test profiles (docs/prereg/FNET_MOTOR.md). One job at a time.
#     sh fnet/stand/run_motor_test.sh
set -e
PY=/d/Claude/fnet-env/Scripts/python.exe
REG=C:/msys64/home/ceo/nai/docs/prereg/FNET_MOTOR.md
L=/d/Claude/nai-data/fnet/motor
cd /c/msys64/home/ceo/nai/fnet/stand
$PY -s -E motor_run.py --side test --registered $REG --features stator --step 60 \
    --models fnet,mlp32,ols,lightgbm_tuned > $L/test_run.log 2>&1
$PY -s -E motor_hypotheses.py --results D:/Claude/nai-data/fnet/results/motor_test_stator_step60 > $L/test_hypotheses.txt 2>&1
echo done
