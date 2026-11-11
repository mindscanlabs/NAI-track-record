#!/bin/sh
# The registered single run on the Panda test trajectories (docs/prereg/FNET_ROBOT.md). One job at a time.
#     sh fnet/stand/run_robot_test.sh
set -e
PY=/d/Claude/fnet-env/Scripts/python.exe
REG=C:/msys64/home/ceo/nai/docs/prereg/FNET_ROBOT.md
L=/d/Claude/nai-data/fnet/robot
cd /c/msys64/home/ceo/nai/fnet/stand
$PY -s -E robot_run.py --side test --registered $REG --joints 1,2,3,4,5,6,7 --combs 0,1,2,3,4,5,6,7,8,9,10,11 \
    --models fnet,lightgbm_tuned,mlp32 --features trig --target residual --rows sub10 > $L/test_run.log 2>&1
$PY -s -E robot_hypotheses.py --results D:/Claude/nai-data/fnet/results/robot_test_trig_residual_sub10 \
    > $L/test_hypotheses.txt 2>&1
echo done
