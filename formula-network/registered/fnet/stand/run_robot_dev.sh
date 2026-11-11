#!/bin/sh
# Development on the Panda training seeds only (robot_run.py --side dev): formulations for the elbow (joint 4),
# combinations 0 and 6, three models. One job at a time.
cd /c/msys64/home/ceo/nai/fnet/stand
PY=/d/Claude/fnet-env/Scripts/python.exe
for v in "raw full sub10" "trig full sub10" "raw residual sub10" "trig residual sub10" "trig residual all"; do
    set -- $v
    $PY -s -E robot_run.py --side dev --joints 4 --combs 0,6 --models fnet,lightgbm_tuned,mlp32 \
        --features $1 --target $2 --rows $3
done
echo done
