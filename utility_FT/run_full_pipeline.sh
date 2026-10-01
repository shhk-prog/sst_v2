#!/bin/bash
set -e

# bitsandbytes が CUDA 13.0 のライブラリ(libnvJitLink.so.13)を見つけられるようにする設定
PYTHON_SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
if [ -d "$PYTHON_SITE_PACKAGES/nvidia/cu13/lib" ]; then
    export LD_LIBRARY_PATH="$PYTHON_SITE_PACKAGES/nvidia/cu13/lib:$LD_LIBRARY_PATH"
fi

# FTからBase Modelを含む全評価（A〜D）まで一括で行うマスタースクリプト
# GPUメモリ(VRAM)の枯渇を防ぐため、1つずつ順番に実行します。

BASE_DIR="/mnt/nas/home/hiromi/src/sst_v2/utility_FT"
cd "$BASE_DIR"

# スクリプトに実行権限を付与
chmod +x run_model*.sh run_eval_*.sh run_all_benchmarks.sh

echo "=========================================="
echo "Phase -1: Installing required dependencies for evaluation"
echo "=========================================="
# math_verify 等の数学評価用ライブラリをインストール
# ※ antlr4-python3-runtime==4.11 は math_verify に必要だが、LLaMA-Factory(omegaconf)は4.9.3を要求するため
#   FT前に必ず 4.9.3 に戻す必要がある（Phase1〜3の各FTスクリプト冒頭で戻す）
pip install math_verify latex2sympy2_extended --no-deps 2>/dev/null || true
pip install "antlr4-python3-runtime==4.11" --no-deps 2>/dev/null || true
pip install "datasets>=3.0.0,<4.0.0" --quiet

# コード評価(mbpp)のためのフラグ設定
export HF_ALLOW_CODE_EVAL=1

# LLaMA-Factory の datasets バージョンチェックを無効化（datasets==4.8.5 によりFTが失敗するのを防ぐ）
export DISABLE_VERSION_CHECK=1

# ※ 各学習スクリプト内のハイパーパラメータを変更した場合は、以下のRUN_IDも合わせて変更してください。
RUN_ID_1="model1_math_ep3.0_bs16_lr2.0e-5"
RUN_ID_2="model2_coding_ep3.0_bs16_lr2.0e-5"
RUN_ID_3="model3_medicine_ep3.0_bs16_lr2.0e-5"

echo "=========================================="
echo "Phase 0: Evaluating BaseModel on All Benchmarks (A to D)"
echo "=========================================="
# ベースモデルの評価を最初に実行します（引数なし）
./run_all_benchmarks.sh

echo "=========================================="
echo "Phase 1: Model 1 (Math) FT & All Benchmarks"
echo "=========================================="
# FT実行前にantlr4を4.9.3(omegaconf/LLaMA-Factory互換バージョン)に戻す
pip install "antlr4-python3-runtime==4.9.3" --no-deps -q 2>/dev/null || true
./run_model1_math.sh
# FT後にmath評価用の4.11に戻す
pip install "antlr4-python3-runtime==4.11" --no-deps -q 2>/dev/null || true
./run_all_benchmarks.sh "$RUN_ID_1"

echo "=========================================="
echo "Phase 2: Model 2 (Coding) FT & All Benchmarks"
echo "=========================================="
pip install "antlr4-python3-runtime==4.9.3" --no-deps -q 2>/dev/null || true
./run_model2_coding.sh
pip install "antlr4-python3-runtime==4.11" --no-deps -q 2>/dev/null || true
./run_all_benchmarks.sh "$RUN_ID_2"

echo "=========================================="
echo "Phase 3: Model 3 (Medicine) FT & All Benchmarks"
echo "=========================================="
pip install "antlr4-python3-runtime==4.9.3" --no-deps -q 2>/dev/null || true
./run_model3_medicine.sh
pip install "antlr4-python3-runtime==4.11" --no-deps -q 2>/dev/null || true
./run_all_benchmarks.sh "$RUN_ID_3"

echo "=========================================="
echo "All FT and Benchmark evaluations (BaseModel + 3 FT models) completed successfully!"
echo "=========================================="
