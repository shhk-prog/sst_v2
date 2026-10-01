#!/bin/bash
set -e

# bitsandbytes が CUDA 13.0 のライブラリ(libnvJitLink.so.13)を見つけられるようにする設定
PYTHON_SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
if [ -d "$PYTHON_SITE_PACKAGES/nvidia/cu13/lib" ]; then
    export LD_LIBRARY_PATH="$PYTHON_SITE_PACKAGES/nvidia/cu13/lib:$LD_LIBRARY_PATH"
fi

# フルスケール一括評価マスタースクリプト
# A(一般/GLUE/数学), B(コーディング), C(通信), D(安全性) のすべての評価を順次実行します。
# 
# 使用法: ./run_all_benchmarks.sh [RUN_ID]
# RUN_IDを省略した場合は BaseModel の評価が走ります。

RUN_ID=$1
BASE_DIR="/mnt/nas/home/hiromi/src/sst_v2/utility_FT"
cd "$BASE_DIR"

echo "=========================================="
echo "Starting Full Scale Benchmarks for: ${RUN_ID:-BaseModel}"
echo "=========================================="

# A. 一般推論・数学・GLUE・医学 (lm-evaluation-harness)
echo "------------------------------------------"
echo "[A] Running lm-evaluation-harness benchmarks"
echo "------------------------------------------"
chmod +x run_eval_all_utility.sh
./run_eval_all_utility.sh "$RUN_ID"

# B. コーディング (bigcode-evaluation-harness)
echo "------------------------------------------"
echo "[B] Running bigcode-evaluation-harness benchmarks"
echo "------------------------------------------"
chmod +x run_eval_coding.sh
./run_eval_coding.sh "$RUN_ID"

# C. 通信・専門ドメイン (TeleQnA)
echo "------------------------------------------"
echo "[C] Running TeleQnA benchmarks"
echo "------------------------------------------"
chmod +x run_eval_telecom.sh
./run_eval_telecom.sh "$RUN_ID"

# D. Safety (安全性・アライメント)
echo "------------------------------------------"
echo "[D] Running Safety benchmarks"
echo "------------------------------------------"
chmod +x run_eval_safety.sh
./run_eval_safety.sh "$RUN_ID"

echo "=========================================="
echo "All benchmarks completed successfully for: ${RUN_ID:-BaseModel}"
echo "=========================================="
