#!/bin/sh
# The registered single run on the fifth suite (docs/prereg/FNET_FIFTH.md): the formula network v14b and v13 (each as
# nai_cli --net with its released settings), the baselines, the compiled size and speed; then the hypotheses. One job
# at a time.
#     sh fnet/stand/run_fifth_test.sh
set -e
PY=/d/Claude/fnet-env/Scripts/python.exe
REG=C:/msys64/home/ceo/nai/docs/prereg/FNET_FIFTH.md
cd /c/msys64/home/ceo/nai/fnet/stand
L=/d/Claude/nai-data/fnet
$PY -s -E fifth_net.py --cli ../build/v14b/nai_cli_v14b.exe --tag v14b --side test --registered $REG \
    > $L/fifth_test_fnet_v14b.log 2>&1
$PY -s -E fifth_net.py --cli ../../bench/results/v26/nai_cli_v26.exe --tag v13 --side test --registered $REG \
    > $L/fifth_test_fnet_v13.log 2>&1
$PY -s -E baselines.py --assignment fifth_assignment.tsv --side test --registered $REG \
    --splits iid1,xfeat,xy,xfeat_lo,xy_lo > $L/fifth_test_baselines.log 2>&1
$PY -s -E fifth_net.py --cli ../build/v14b/nai_cli_v14b.exe --tag v14b --side test --registered $REG --size \
    > $L/fifth_test_size.log 2>&1
$PY -s -E fifth_hypotheses.py --side test --net fnet_v14b --old fnet_v13 > $L/fifth_test_hypotheses.txt 2>&1
$PY -s -E compare.py --suite fifth_ --side test > $L/fifth_test_compare.txt 2>&1
echo done
