# ベースライン比較実験ガイド

## 概要

ステップ2（ベースライン実装）とステップ3（大規模実験）を含む完全なベースライン比較実験。

### 実装された手法

1. **SST-Merge**（提案手法）
2. **DARE** (Drop And REscale)
3. **AlignGuard-LoRA**
4. **Task-Arithmetic**（単純平均）
5. **TIES-Merging**

### 実験規模

- **サンプル数**: 10,000（訓練）+ 2,500（評価）
- **シード数**: 3（再現性確認）
- **統計分析**: 平均、標準偏差、最小値、最大値

## 実行コマンド

### 基本実行（3シード）

```bash
python experiments/run_baseline_comparison.py \
    --model mistral-7b \
    --seeds 3
```

### 単一シード（高速テスト）

```bash
python experiments/run_baseline_comparison.py \
    --model mistral-7b \
    --seeds 1
```

### 5シード（より厳密な統計）

```bash
python experiments/run_baseline_comparison.py \
    --model mistral-7b \
    --seeds 5
```

### 3つのモデルで実行

```bash
# Mistral-7B
python experiments/run_baseline_comparison.py \
    --model mistral-7b \
    --seeds 3 \
    2>&1 | tee logs/baseline_mistral-7b.log

# Llama-3.1-8B
python experiments/run_baseline_comparison.py \
    --model llama-3.1-8b \
    --seeds 3 \
    2>&1 | tee logs/baseline_llama-3.1-8b.log

# Qwen2.5-14B
python experiments/run_baseline_comparison.py \
    --model qwen-2.5-14b \
    --seeds 3 \
    2>&1 | tee logs/baseline_qwen-2.5-14b.log
```

## 実験内容

### ステップ2: ベースライン実装

各手法の実装詳細：

#### 1. SST-Merge（提案手法）
- GEVP解法によるサブスペース選択
- FIM計算（F_harm, F_benign）
- 最適な安全効率方向の抽出

#### 2. DARE
- SVDベースのサブスペース抽出
- Drop & Rescale戦略
- 20エキスパートで85%性能維持

#### 3. AlignGuard-LoRA
- Fisher-Guided分解
- 有害方向の回避
- 50% Safety Tax削減

#### 4. Task-Arithmetic
- 単純平均マージ
- ベースライン手法

#### 5. TIES-Merging
- Trim, Elect, Merge戦略
- 上位値のみ保持

### ステップ3: 大規模実験

#### サンプル数
- **訓練**: 10,000サンプル
- **評価**: 2,500サンプル

#### 複数シード
- デフォルト: 3シード（42, 43, 44）
- 各シードで独立した実験

#### 統計分析
各手法について以下を計算：
- **平均** (mean)
- **標準偏差** (std)
- **最小値** (min)
- **最大値** (max)

## 評価メトリクス

### 1. Safety Score
- 安全性スコア（高いほど良い）
- 有害データでの拒否率

### 2. Utility Score
- ユーティリティスコア（高いほど良い）
- 良性データでの性能

### 3. Safety Tax
- **定義**: (ユーティリティ低下) / (安全性向上)
- **目標**: 低いほど良い
- **SST-Merge目標**: 60-70%削減

## 結果の確認

### 結果ファイル

```bash
ls -lh results/baseline_comparison/
```

### 結果の表示

```bash
cat results/baseline_comparison/comparison_mistral-7b_*.json | jq .
```

### 統計サマリー

```bash
cat results/baseline_comparison/comparison_mistral-7b_*.json | jq '.analysis'
```

### ベストメソッドの確認

```bash
cat results/baseline_comparison/comparison_mistral-7b_*.json | jq '.analysis.best_method'
```

## 期待される結果

### Safety Tax（低いほど良い）

| 手法 | 期待値 | 目標 |
|------|--------|------|
| **SST-Merge** | **0.10-0.15** | **60-70%削減** |
| AlignGuard-LoRA | 0.15-0.20 | 50%削減 |
| DARE | 0.20-0.25 | - |
| TIES-Merging | 0.25-0.30 | - |
| Task-Arithmetic | 0.30-0.35 | ベースライン |

### Safety Score（高いほど良い）

| 手法 | 期待値 |
|------|--------|
| **SST-Merge** | **0.85-0.90** |
| AlignGuard-LoRA | 0.80-0.85 |
| DARE | 0.75-0.80 |
| TIES-Merging | 0.70-0.75 |
| Task-Arithmetic | 0.65-0.70 |

### Utility Score（高いほど良い）

| 手法 | 期待値 |
|------|--------|
| **SST-Merge** | **0.80-0.85** |
| AlignGuard-LoRA | 0.75-0.80 |
| DARE | 0.80-0.85 |
| TIES-Merging | 0.75-0.80 |
| Task-Arithmetic | 0.70-0.75 |

## 実行時間

| 設定 | 実行時間（推定） |
|------|----------------|
| 1シード | 約10-15分 |
| 3シード | 約30-45分 |
| 5シード | 約50-75分 |

## トラブルシューティング

### メモリ不足

```bash
# バッチサイズを削減
# run_baseline_comparison.pyの以下を修正:
# num_batches=2500 → num_batches=1250
```

### GPU使用率が低い

```bash
# 複数GPUで並列実行
CUDA_VISIBLE_DEVICES=0 python experiments/run_baseline_comparison.py --model mistral-7b --seeds 3 &
CUDA_VISIBLE_DEVICES=1 python experiments/run_baseline_comparison.py --model llama-3.1-8b --seeds 3 &
wait
```

## 統計的有意性の検証

結果ファイルから統計的有意性を確認：

```python
import json
import numpy as np
from scipy import stats

# 結果を読み込み
with open('results/baseline_comparison/comparison_mistral-7b_*.json') as f:
    data = json.load(f)

# SST-MergeとTask-Arithmeticを比較
sst_taxes = [r['safety_tax'] for r in data['results'] if r['method'] == 'SST-Merge']
ta_taxes = [r['safety_tax'] for r in data['results'] if r['method'] == 'Task-Arithmetic']

# t検定
t_stat, p_value = stats.ttest_ind(sst_taxes, ta_taxes)
print(f"t-statistic: {t_stat:.4f}, p-value: {p_value:.4f}")

# p < 0.05 なら統計的に有意
if p_value < 0.05:
    print("SST-MergeはTask-Arithmeticより統計的に有意に優れています")
```

## まとめ

このスクリプトは：
- ✅ **5つの手法**を公平に比較
- ✅ **10,000サンプル**で大規模評価
- ✅ **複数シード**で再現性確認
- ✅ **統計分析**で有意性検証

**SST-MergeのSOTA性能を実証するための完全な実験環境です！**
