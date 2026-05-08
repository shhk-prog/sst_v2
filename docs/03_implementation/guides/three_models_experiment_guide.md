# 3つのモデルで完全な実験を実行する方法

## 概要

Mistral-7B、Llama-3.1-8B、Qwen2.5-14Bの3つのモデルで完全な実験を実行し、包括的な比較結果を得る方法を説明します。

## 実行方法

### オプション1: すべてのモデルを一度に実行（推奨）

**実行時間**: 約9-18時間（GPU性能による）

```bash
# すべてのモデルで全実験を実行
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all
```

このコマンドは以下を実行します:
1. Mistral-7Bで実験1-3を実行
2. Llama-3.1-8Bで実験1-3を実行
3. Qwen2.5-14Bで実験1-3を実行

### オプション2: モデルごとに個別実行

各モデルを個別に実行する場合:

#### Mistral-7B（最も軽量）

**実行時間**: 約3-6時間  
**VRAM**: 約16GB

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_mistral-7b.log
```

#### Llama-3.1-8B-Instruct（高品質）

**実行時間**: 約4-7時間  
**VRAM**: 約18GB

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model llama-3.1-8b \
    --experiment all \
    2>&1 | tee logs/full_llama-3.1-8b.log
```

#### Qwen2.5-14B-Instruct（最大モデル）

**実行時間**: 約5-8時間  
**VRAM**: 約32GB

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model qwen-2.5-14b \
    --experiment all \
    2>&1 | tee logs/full_qwen-2.5-14b.log
```

### オプション3: 並列実行（複数GPU使用）

複数のGPUがある場合、並列実行で時間を短縮できます:

```bash
# ターミナル1（GPU 0）
CUDA_VISIBLE_DEVICES=0 python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_mistral-7b.log &

# ターミナル2（GPU 1）
CUDA_VISIBLE_DEVICES=1 python experiments/run_real_experiments.py \
    --mode full \
    --model llama-3.1-8b \
    --experiment all \
    2>&1 | tee logs/full_llama-3.1-8b.log &

# ターミナル3（GPU 2）
CUDA_VISIBLE_DEVICES=2 python experiments/run_real_experiments.py \
    --mode full \
    --model qwen-2.5-14b \
    --experiment all \
    2>&1 | tee logs/full_qwen-2.5-14b.log &

# すべてのジョブが完了するまで待機
wait
```

**実行時間**: 約5-8時間（最も遅いモデルに依存）

## 実行前の準備

### 1. ログディレクトリの作成

```bash
mkdir -p logs
```

### 2. ディスク容量の確認

```bash
df -h .
# 必要容量: 約50-100GB（モデル + データセット + 結果）
```

### 3. GPU状態の確認

```bash
nvidia-smi

# 期待される出力:
# - 利用可能なGPU: 1-4枚
# - 空きVRAM: Mistral(16GB), Llama(18GB), Qwen(32GB)
```

## 実行中のモニタリング

### リアルタイムログの確認

```bash
# 別のターミナルで
tail -f logs/full_mistral-7b.log
tail -f logs/full_llama-3.1-8b.log
tail -f logs/full_qwen-2.5-14b.log
```

### GPU使用状況の監視

```bash
# 1秒ごとにGPU状態を更新
watch -n 1 nvidia-smi
```

### 進捗状況の確認

```bash
# 実験1の進捗
grep "EXPERIMENT 1" logs/full_*.log

# 実験2の進捗
grep "EXPERIMENT 2" logs/full_*.log

# 実験3の進捗
grep "EXPERIMENT 3" logs/full_*.log

# 完了確認
grep "ALL EXPERIMENTS COMPLETED" logs/full_*.log
```

## 結果の確認

### 結果ファイルの構造

```
results/
├── exp1_safety_utility/
│   ├── exp1_results_*_mistral-7b.json
│   ├── exp1_results_*_llama-3.1-8b.json
│   └── exp1_results_*_qwen-2.5-14b.json
├── exp2_multitask/
│   ├── exp2_results_*_mistral-7b.json
│   ├── exp2_results_*_llama-3.1-8b.json
│   └── exp2_results_*_qwen-2.5-14b.json
└── exp3_baseline/
    ├── exp3_results_*_mistral-7b.json
    ├── exp3_results_*_llama-3.1-8b.json
    └── exp3_results_*_qwen-2.5-14b.json
```

### 結果の比較

```bash
# 実験1の結果を比較
echo "=== Mistral-7B ==="
cat results/exp1_safety_utility/exp1_results_*_mistral-7b.json | jq '{safety: .safety.refusal_rate, utility: .utility.accuracy}'

echo "=== Llama-3.1-8B ==="
cat results/exp1_safety_utility/exp1_results_*_llama-3.1-8b.json | jq '{safety: .safety.refusal_rate, utility: .utility.accuracy}'

echo "=== Qwen2.5-14B ==="
cat results/exp1_safety_utility/exp1_results_*_qwen-2.5-14b.json | jq '{safety: .safety.refusal_rate, utility: .utility.accuracy}'
```

### 実験3（ベースライン比較）の結果

```bash
# SST-Mergeのスコアを比較
echo "=== SST-Merge Performance Comparison ==="
for model in mistral-7b llama-3.1-8b qwen-2.5-14b; do
    echo "--- $model ---"
    cat results/exp3_baseline/exp3_results_*_${model}.json | jq '.["SST-Merge"]'
done
```

## 計算時間とリソースの見積もり

### 単一GPU実行（順次）

| モデル | 実験1 | 実験2 | 実験3 | 合計 |
|--------|-------|-------|-------|------|
| Mistral-7B | 1-2h | 0.5-1h | 1-2h | 3-6h |
| Llama-3.1-8B | 1.5-2.5h | 0.5-1h | 1.5-2.5h | 4-7h |
| Qwen2.5-14B | 2-3h | 0.5-1h | 2-3h | 5-8h |
| **全体** | - | - | - | **12-21h** |

### 複数GPU並列実行

| 構成 | 実行時間 |
|------|---------|
| 3 GPU（各モデル1つずつ） | 5-8h |
| 2 GPU（2モデル並列 + 1モデル順次） | 8-13h |
| 1 GPU（順次実行） | 12-21h |

### VRAM要件

| モデル | 最小VRAM | 推奨VRAM | バッチサイズ |
|--------|----------|----------|-------------|
| Mistral-7B | 14GB | 16GB+ | 32 |
| Llama-3.1-8B | 16GB | 18GB+ | 32 |
| Qwen2.5-14B | 28GB | 32GB+ | 32 |

## トラブルシューティング

### メモリ不足エラー

```bash
# バッチサイズを減らす
# configs/experiment_config_real.yaml を編集
# batch_size: 32 → 16 または 8
```

### 実行が途中で停止した場合

```bash
# 特定のモデルから再開
python experiments/run_real_experiments.py \
    --mode full \
    --model llama-3.1-8b \
    --experiment all
```

### 特定の実験のみ再実行

```bash
# 実験1のみ再実行
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment exp1
```

## 推奨実行フロー

### ステップ1: 動作確認（最小構成）

```bash
# 各モデルで最小構成テスト（約30分）
python experiments/run_real_experiments.py \
    --mode minimal \
    --model all \
    --experiment all
```

### ステップ2: 単一モデルでフルスケール

```bash
# Mistral-7Bでフルスケール（約3-6時間）
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_mistral-7b.log
```

### ステップ3: 全モデルでフルスケール

```bash
# すべてのモデルで実行（約12-21時間）
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all \
    2>&1 | tee logs/full_all_models.log
```

## 結果の分析

### 包括的な比較レポートの生成

実験完了後、以下のスクリプトで包括的な比較レポートを生成できます:

```bash
# 比較レポート生成（将来実装予定）
python scripts/generate_comparison_report.py \
    --models mistral-7b llama-3.1-8b qwen-2.5-14b \
    --output results/comprehensive_comparison.md
```

### 手動での結果確認

```bash
# すべての結果ファイルを確認
find results -name "*.json" -type f | sort

# 最新の結果のみ表示
find results -name "*.json" -type f -mtime -1 | sort
```

## クイックリファレンス

```bash
# 完全な実験（推奨）
python experiments/run_real_experiments.py --mode full --model all --experiment all

# 並列実行（3 GPU）
CUDA_VISIBLE_DEVICES=0 python experiments/run_real_experiments.py --mode full --model mistral-7b --experiment all &
CUDA_VISIBLE_DEVICES=1 python experiments/run_real_experiments.py --mode full --model llama-3.1-8b --experiment all &
CUDA_VISIBLE_DEVICES=2 python experiments/run_real_experiments.py --mode full --model qwen-2.5-14b --experiment all &
wait

# 進捗確認
tail -f logs/full_*.log
watch -n 1 nvidia-smi

# 結果確認
ls -lh results/exp*/
cat results/exp3_baseline/exp3_results_*.json | jq '.["SST-Merge"]'
```

## 期待される結果

### 実験1: Safety Tax

各モデルで以下のメトリクスが得られます:
- 安全性スコア（拒否率）
- ユーティリティスコア（精度）
- Safety Tax

### 実験2: マルチタスク干渉耐性

各モデルで異なるエキスパート数（8, 12, 16, 20）での性能維持率

### 実験3: ベースライン比較

各モデルで5つの手法（TA、TIES、DARE、AGL、SST-Merge）の比較結果

**期待される傾向**:
- SST-Mergeが最高の安全性スコアを達成
- ユーティリティを高いレベルで維持
- パレート最適に最も近い

## まとめ

3つのモデルで完全な実験を実行するには:

1. **推奨方法**: `--model all --experiment all`で一度に実行
2. **実行時間**: 12-21時間（順次）、5-8時間（並列）
3. **リソース**: GPU 1-3枚、VRAM 16-32GB
4. **結果**: 各モデルで3つの実験の完全な結果が得られる

準備ができたら実行を開始してください！
