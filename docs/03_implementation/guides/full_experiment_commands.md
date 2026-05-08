# 完全なフル実験コマンドガイド

## 概要

SST-Mergeには2種類の実験スクリプトがあります：

1. **`run_real_experiments.py`**: 簡易実験とフル実験（実験1のみ完全）
2. **`run_full_experiments.py`**: **完全なフル実験**（実験2と3も実際にマージングと評価）

## 完全なフル実験（推奨）

### 実験2: マルチタスク干渉耐性

**実行内容**:
- ✅ 実際のLoRAアダプターを作成
- ✅ SST-Mergeで実際にマージ
- ✅ マージ後のモデルを実際に評価（安全性 + ユーティリティ）

```bash
# 実験2のみ実行
python experiments/run_full_experiments.py \
    --model mistral-7b \
    --experiment exp2

# ログ付き
python experiments/run_full_experiments.py \
    --model mistral-7b \
    --experiment exp2 \
    2>&1 | tee logs/full_exp2_mistral-7b.log
```

**実行時間**: 約30-60分

### 実験3: ベースライン比較

**実行内容**:
- ✅ すべての手法（SST-Merge, DARE, AGL, Simple-Average）で実際にマージ
- ✅ マージ後のモデルを実際に評価
- ✅ MetricsReporterで分析とレポート生成

```bash
# 実験3のみ実行
python experiments/run_full_experiments.py \
    --model mistral-7b \
    --experiment exp3

# ログ付き
python experiments/run_full_experiments.py \
    --model mistral-7b \
    --experiment exp3 \
    2>&1 | tee logs/full_exp3_mistral-7b.log
```

**実行時間**: 約1-2時間

### 実験2と3を両方実行

```bash
python experiments/run_full_experiments.py \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_exp_all_mistral-7b.log
```

**実行時間**: 約1.5-3時間

## 3つのモデルで完全なフル実験

### 順次実行

```bash
# Mistral-7B
python experiments/run_full_experiments.py \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_exp_mistral-7b.log

# Llama-3.1-8B
python experiments/run_full_experiments.py \
    --model llama-3.1-8b \
    --experiment all \
    2>&1 | tee logs/full_exp_llama-3.1-8b.log

# Qwen2.5-14B
python experiments/run_full_experiments.py \
    --model qwen-2.5-14b \
    --experiment all \
    2>&1 | tee logs/full_exp_qwen-2.5-14b.log
```

**合計実行時間**: 約4.5-9時間

### 並列実行（複数GPU使用）

```bash
# GPU 0: Mistral-7B
CUDA_VISIBLE_DEVICES=0 python experiments/run_full_experiments.py \
    --model mistral-7b --experiment all \
    2>&1 | tee logs/full_exp_mistral-7b.log &

# GPU 1: Llama-3.1-8B
CUDA_VISIBLE_DEVICES=1 python experiments/run_full_experiments.py \
    --model llama-3.1-8b --experiment all \
    2>&1 | tee logs/full_exp_llama-3.1-8b.log &

# GPU 2: Qwen2.5-14B
CUDA_VISIBLE_DEVICES=2 python experiments/run_full_experiments.py \
    --model qwen-2.5-14b --experiment all \
    2>&1 | tee logs/full_exp_qwen-2.5-14b.log &

wait
```

**合計実行時間**: 約1.5-3時間（並列実行）

## 簡易実験（動作確認用）

動作確認のみの場合は、従来の`run_real_experiments.py`を使用：

```bash
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all
```

## 実験内容の比較

### run_real_experiments.py（従来）

| 実験 | minimal | full |
|------|---------|------|
| **実験1** | 100サンプル評価 | 10,000サンプル評価 |
| **実験2** | ダミーデータ | SST-Mergeマージング（評価なし） |
| **実験3** | ランダムデータ | SST-Mergeのみ評価 |

### run_full_experiments.py（新規・推奨）

| 実験 | 実行内容 |
|------|---------|
| **実験2** | ✅ 実際のLoRAマージング + 評価 |
| **実験3** | ✅ 全手法でマージング + 評価 |

## 結果の確認

### 完全なフル実験の結果

```bash
# 実験2の結果
ls -lh results/exp2_multitask_full/
cat results/exp2_multitask_full/exp2_full_results_*.json | jq .

# 実験3の結果
ls -lh results/exp3_baseline_full/
cat results/exp3_baseline_full/exp3_full_results_*.json | jq .

# SST-Mergeのスコア確認
cat results/exp3_baseline_full/exp3_full_results_*.json | jq '.["SST-Merge"]'
```

### 簡易実験の結果

```bash
ls -lh results/exp*/
cat results/exp1_safety_utility/exp1_results_*.json | jq .
```

## 推奨実行フロー

### ステップ1: 動作確認（簡易実験）

```bash
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all
```

**実行時間**: 約10-30分

### ステップ2: 単一モデルで完全なフル実験

```bash
python experiments/run_full_experiments.py \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_exp_mistral-7b.log
```

**実行時間**: 約1.5-3時間

### ステップ3: 全モデルで完全なフル実験

```bash
# 並列実行（推奨）
CUDA_VISIBLE_DEVICES=0 python experiments/run_full_experiments.py --model mistral-7b --experiment all &
CUDA_VISIBLE_DEVICES=1 python experiments/run_full_experiments.py --model llama-3.1-8b --experiment all &
CUDA_VISIBLE_DEVICES=2 python experiments/run_full_experiments.py --model qwen-2.5-14b --experiment all &
wait
```

**実行時間**: 約1.5-3時間

## クイックリファレンス

```bash
# 完全なフル実験（実験2と3）
python experiments/run_full_experiments.py --model mistral-7b --experiment all

# 実験2のみ（マルチタスク干渉耐性）
python experiments/run_full_experiments.py --model mistral-7b --experiment exp2

# 実験3のみ（ベースライン比較）
python experiments/run_full_experiments.py --model mistral-7b --experiment exp3

# 簡易実験（動作確認）
python experiments/run_real_experiments.py --mode minimal --model mistral-7b --experiment all

# 進捗確認
tail -f logs/full_exp_*.log
watch -n 1 nvidia-smi
```

## まとめ

| スクリプト | 用途 | 実験2 | 実験3 |
|-----------|------|-------|-------|
| **run_full_experiments.py** | **完全なフル実験** | **実際のマージング + 評価** | **全手法でマージング + 評価** |
| run_real_experiments.py | 簡易実験・動作確認 | ダミーデータ | SST-Mergeのみ評価 |

**論文用データや完全な評価には`run_full_experiments.py`を使用してください！** ✅
