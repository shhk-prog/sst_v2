#!/bin/bash
# SST-Merge V2 実験スクリプト
# 複数のモードと設定でマージを実行し、比較実験を行う

set -e

MODEL="llama-3.1-8b"
VARIANTS=("A5+A7" "A6+A7" "A5+A6+A7")
MODES=("direct" "residual" "layerwise")
RESIDUAL_RATIOS=(0.5 0.7 0.9)
SAFETY_WEIGHTS=(0.5 1.0 1.5)

echo "=============================================="
echo "SST-MERGE V2 EXPERIMENT SUITE"
echo "=============================================="
echo "Model: $MODEL"
echo "Variants: ${VARIANTS[*]}"
echo "Modes: ${MODES[*]}"
echo "=============================================="

# 1. Direct mode（ベースライン相当）
echo ""
echo "=== Phase 1: Direct Mode (Baseline Equivalent) ==="
for variant in "${VARIANTS[@]}"; do
    echo "Running: $variant with direct mode..."
    python scripts/run_merge.py \
        --model "$MODEL" \
        --variant "$variant" \
        --mode direct \
        --safety_weight 1.0
done

# 2. Residual mode（推奨設定）
echo ""
echo "=== Phase 2: Residual Mode (Recommended) ==="
for variant in "${VARIANTS[@]}"; do
    for ratio in "${RESIDUAL_RATIOS[@]}"; do
        echo "Running: $variant with residual mode (r=$ratio)..."
        python scripts/run_merge.py \
            --model "$MODEL" \
            --variant "$variant" \
            --mode residual \
            --residual_ratio "$ratio" \
            --safety_weight 1.0
    done
done

# 3. Safety weight variation
echo ""
echo "=== Phase 3: Safety Weight Variation ==="
for weight in "${SAFETY_WEIGHTS[@]}"; do
    echo "Running: A5+A7 with direct mode (w=$weight)..."
    python scripts/run_merge.py \
        --model "$MODEL" \
        --variant "A5+A7" \
        --mode direct \
        --safety_weight "$weight"
done

# 4. Layer-wise mode with presets
echo ""
echo "=== Phase 4: Layer-wise Mode with Presets ==="
PRESETS=("safety_first" "balanced" "utility_first" "minimal")
for preset in "${PRESETS[@]}"; do
    echo "Running: A5+A7 with layerwise mode (preset=$preset)..."
    python scripts/run_merge.py \
        --model "$MODEL" \
        --variant "A5+A7" \
        --mode layerwise \
        --preset "$preset" \
        --safety_weight 1.0 \
        --use_fim
done

echo ""
echo "=============================================="
echo "ALL EXPERIMENTS COMPLETED"
echo "=============================================="
echo "Results saved to: results/$MODEL/"
echo ""
echo "Next steps:"
echo "1. Evaluate each adapter:"
echo "   python scripts/evaluate.py --adapter results/$MODEL/<adapter>.pt"
echo "2. Compare results and select best configuration"
echo "=============================================="
