#!/bin/sh
# Development, step 2 (training seeds only): every joint, the residual target, raw or trig inputs, combinations
# 0 and 6, three models. The formulation for the registration is chosen from these (mean nMSE over the joints).
cd /c/msys64/home/ceo/nai/fnet/stand
PY=/d/Claude/fnet-env/Scripts/python.exe
for f in raw trig; do
    $PY -s -E robot_run.py --side dev --joints 1,2,3,4,5,6,7 --combs 0,6 --models fnet,lightgbm_tuned,mlp32 \
        --features $f --target residual --rows sub10
done
echo done
