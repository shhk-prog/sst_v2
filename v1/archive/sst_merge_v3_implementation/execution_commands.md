# SST-Merge Phase 1-3 実行コマンド完全版

## 環境準備

```bash
cd /mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v2
source ../sst/bin/activate
```

---

## Phase 1: 基本修正（Residual Ratio削除）

### 1-1. マージ実行（k=10）

```bash
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 10 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim
```

**実行時間**: 約10-15分（FIM計算含む）

### 1-2. 評価実行

```bash
python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_*.pt \
    --model llama-3.1-8b \
    --max_samples 500
```

**実行時間**: 約40-50分

### 1-3. 結果確認

```bash
# 最新の評価結果を確認
ls -lt results/llama-3.1-8b/*.eval.json | head -1

# 結果を表示
cat results/llama-3.1-8b/sst_v2_A5_A7_*.eval.json | jq '.results | {
    jailbreak: .jailbreak.jailbreak_resistance,
    mmlu: .mmlu.accuracy,
    repliqa: .repliqa.rouge_l,
    beavertails: {
        refusal_rate: .beavertails.refusal_rate,
        harmful_rate: .beavertails.harmful_response_rate
    }
}'
```

**期待結果**: Jailbreak 77%+, MMLU 52%+, RepliQA 40%+

---

## Phase 2: kパラメータ最適化

### 2-1. グリッドサーチ実行

```bash
# k=20
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 20 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k20_*.pt \
    --model llama-3.1-8b \
    --max_samples 500

# k=30
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 30 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k30_*.pt \
    --model llama-3.1-8b \
    --max_samples 500

# k=50
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 50 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k50_*.pt \
    --model llama-3.1-8b \
    --max_samples 500

# k=100
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 100 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k100_*.pt \
    --model llama-3.1-8b \
    --max_samples 500

# k=200
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 200 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k200_*.pt \
    --model llama-3.1-8b \
    --max_samples 500
```

**実行時間**: 各k値につき約50-60分

### 2-2. 結果比較

```bash
# 全結果を比較
echo "=== k Parameter Comparison ==="
for k in 10 20 30 50 100 200; do
    echo "k=$k:"
    cat results/llama-3.1-8b/*_k${k}_*.eval.json 2>/dev/null | jq -r '
        "  Jailbreak: \(.results.jailbreak.jailbreak_resistance * 100 | round)%",
        "  MMLU: \(.results.mmlu.accuracy * 100 | round)%",
        "  RepliQA: \(.results.repliqa.rouge_l * 100 | round)%"
    ' || echo "  Not found"
done
```

**期待結果**: k↑ → Jailbreak↑, Utility維持

### 2-3. 最適なk決定

```bash
# 目標: Jailbreak 85-95%, MMLU 52%+, RepliQA 38%+
# 最適なkを選択（例: k=50）
```

---

## Phase 3: レイヤー別最適化（オプション）

### 3-1. レイヤー別設定でマージ

```bash
# レイヤー別k設定を使用（今後実装予定）
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --use_layer_config \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim
```

### 3-2. 評価

```bash
python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_layerwise_*.pt \
    --model llama-3.1-8b \
    --max_samples 500
```

**期待結果**: Jailbreak 98%+, MMLU 52%+, RepliQA 40%+

---

## 一括実行スクリプト

### Phase 1のみ

```bash
#!/bin/bash
cd /mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v2
source ../sst/bin/activate

# Phase 1: k=10
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 10 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_*.pt \
    --model llama-3.1-8b \
    --max_samples 500

# 結果表示
cat results/llama-3.1-8b/*.eval.json | tail -1 | jq '.results'
```

### Phase 2グリッドサーチ

```bash
#!/bin/bash
cd /mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v2
source ../sst/bin/activate

for k in 20 30 50 100 200; do
    echo "=== Running k=$k ==="
    
    # マージ
    python scripts/run_merge.py \
        --model llama-3.1-8b \
        --variant A5+A7 \
        --k $k \
        --safety_weight 1.0 \
        --max_samples 500 \
        --use_fim
    
    # 評価
    ADAPTER=$(ls -t results/llama-3.1-8b/sst_v2_A5_A7_*.pt | head -1)
    python scripts/evaluate.py \
        --adapter $ADAPTER \
        --model llama-3.1-8b \
        --max_samples 500
    
    echo "=== k=$k completed ==="
done

# 結果比較
echo "=== Final Results ==="
for k in 10 20 30 50 100 200; do
    echo "k=$k:"
    cat results/llama-3.1-8b/*_k${k}_*.eval.json 2>/dev/null | jq -r '
        "  Jailbreak: \(.results.jailbreak.jailbreak_resistance * 100 | round)%",
        "  MMLU: \(.results.mmlu.accuracy * 100 | round)%",
        "  RepliQA: \(.results.repliqa.rouge_l * 100 | round)%"
    ' || echo "  Not found"
done
```

---

## クイックスタート（推奨）

```bash
# 1. 環境準備
cd /mnt/iag-02/home/hiromi/src/SST_merge/sst_merge_v2
source ../sst/bin/activate

# 2. Phase 1実行（k=10）
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 10 --safety_weight 1.0 --max_samples 500 --use_fim
python scripts/evaluate.py --adapter results/llama-3.1-8b/sst_v2_A5_A7_*.pt --model llama-3.1-8b --max_samples 500

# 3. 結果確認
ls -lt results/llama-3.1-8b/*.eval.json | head -1
cat results/llama-3.1-8b/*.eval.json | tail -1 | jq '.results | {jailbreak: .jailbreak.jailbreak_resistance, mmlu: .mmlu.accuracy, repliqa: .repliqa.rouge_l}'

# 4. Phase 2実行（k=50推奨）
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 50 --safety_weight 1.0 --max_samples 500 --use_fim
python scripts/evaluate.py --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k50_*.pt --model llama-3.1-8b --max_samples 500
```

---

## トラブルシューティング

### アダプターファイルが見つからない

```bash
# 最新のアダプターを確認
ls -lt results/llama-3.1-8b/sst_v2_*.pt | head -5

# ファイル名を直接指定
python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_residual_r0.7_w1.0_20260105_232405.pt \
    --model llama-3.1-8b \
    --max_samples 500
```

### メモリ不足

```bash
# max_samplesを減らす
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 10 --safety_weight 1.0 --max_samples 100 --use_fim
```

### 実行時間を短縮

```bash
# max_samples=100で高速テスト
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 10 --safety_weight 1.0 --max_samples 100 --use_fim
python scripts/evaluate.py --adapter results/llama-3.1-8b/sst_v2_*.pt --model llama-3.1-8b --max_samples 100
```
