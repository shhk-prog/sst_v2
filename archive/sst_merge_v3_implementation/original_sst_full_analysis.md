# 元のSST-Merge (A5+A7) 全結果分析

## データソース

- **JSONLファイル**: 125ファイル
- **ユニーク設定**: 27パターン
- **データソース**: aggregated_results.json + JSONL分析

---

## 全結果一覧（aggregated_results.jsonより）

| k  | α   | Jailbreak | MMLU | RepliQA | Refusal | 評価 |
|----|-----|-----------|------|---------|---------|------|
| 3  | 1.0 | 75.8%     | 52.3% | **40.5%** | 2.0%    | ほぼ達成 |
| 5  | 0.5 | 57.4%     | 55.9% | 0.0%*   | 11.8%   | データ不足 |
| 10 | 0.8 | 70.6%     | 54.0% | 32.4%   | 6.0%    | RepliQA低い |
| **20** | **1.0** | **77.6%** ✓ | **52.9%** ✓ | **40.5%** ✓ | **2.0%** | **全目標達成** ✅ |

*RepliQA 0.0%はデータ欠損と推測

---

## JSONLファイルから確認できた追加設定

### RepliQAのみ利用可能（Jailbreak/MMLUはaggregated_results.jsonより）

| k  | α   | samples | RepliQA | 傾向 |
|----|-----|---------|---------|------|
| 5  | 1.0 | unknown | 40.5%   | 良好 |
| 10 | 0.8 | unknown | 32.4%   | 低い |
| 10 | 0.9 | unknown | 30.2%   | 低い |
| 10 | 1.0 | unknown | 32.6%   | 低い |
| 15 | 0.9 | unknown | 30.6%   | 低い |
| 15 | 1.0 | unknown | 32.7%   | 低い |
| 20 | 0.5 | unknown | 15.0%   | 非常に低い |
| 20 | 0.7 | unknown | 24.5%   | 低い |
| 20 | 0.9 | unknown | 31.1%   | 低い |
| 20 | 1.0 | unknown | 32.6%   | 低い |
| 20 | 1.5 | unknown | 9.2%    | 非常に低い |
| 20 | 2.0 | unknown | 0.8%    | 非常に低い |
| 22 | 0.9 | unknown | 30.3%   | 低い |
| 30 | 0.5 | unknown | 15.3%   | 低い |
| 30 | 0.7 | unknown | 24.3%   | 低い |
| 30 | 0.9 | unknown | 31.4%   | 低い |
| 30 | 1.0 | unknown | 33.7%   | やや低い |
| 40 | 1.0 | unknown | 33.5%   | やや低い |
| 50 | 0.5 | unknown | 15.4%   | 低い |
| 50 | 0.7 | unknown | 24.6%   | 低い |
| 50 | 0.8 | unknown | 28.2%   | 低い |
| 50 | 0.9 | unknown | 30.5%   | 低い |
| 50 | 1.0 | unknown | 33.0%   | やや低い |
| 100 | 10.0 | unknown | 0.5%   | 非常に低い |

---

## 重要な発見

### 1. RepliQAは非常に変動しやすい

**k=3, α=1.0**: RepliQA 40.5% ✓
**k=5, α=1.0**: RepliQA 40.5% ✓
**k=10, α=0.8**: RepliQA 32.4%
**k=20, α=1.0**: RepliQA 32.6% (JSONL) vs 40.5% (aggregated)

**矛盾**: 
- aggregated_results.json: k=20, α=1.0で40.5%
- JSONLファイル: k=20, α=1.0で32.6%

**可能性**:
- aggregated_results.jsonは特定のサンプル数（s=1000?）の結果
- JSONLファイルは別のサンプル数（s=500?）の結果

### 2. αの影響

| α   | RepliQA (k=20) | 傾向 |
|-----|----------------|------|
| 0.5 | 15.0%          | 非常に低い |
| 0.7 | 24.5%          | 低い |
| 0.9 | 31.1%          | やや低い |
| 1.0 | 32.6%          | やや低い |
| 1.5 | 9.2%           | 非常に低い |
| 2.0 | 0.8%           | 非常に低い |

**傾向**:
- α=0.9-1.0が最良
- α<0.9: RepliQA大幅低下
- α>1.0: RepliQA大幅低下

### 3. kの影響

| k  | RepliQA (α=1.0) | 傾向 |
|----|-----------------|------|
| 3  | 40.5%           | 最良 |
| 5  | 40.5%           | 最良 |
| 10 | 32.6%           | 低下 |
| 15 | 32.7%           | 低下 |
| 20 | 32.6%           | 低下 |
| 30 | 33.7%           | やや改善 |
| 40 | 33.5%           | やや改善 |
| 50 | 33.0%           | やや改善 |

**傾向**:
- k=3-5が最良
- k=10-20で大幅低下
- k=30-50でやや回復

---

## V2との比較

### 元のSST-Merge (k=20, α=1.0)

| メトリクス | aggregated | JSONL | 平均 |
|-----------|------------|-------|------|
| Jailbreak | 77.6% | ? | 77.6% |
| MMLU | 52.9% | ? | 52.9% |
| RepliQA | 40.5% | 32.6% | 36.6% |

### V2 (k=20, w=1.0, s=500)

| メトリクス | V2 | 差分 (vs aggregated) |
|-----------|-----|---------------------|
| Jailbreak | 78.2% | +0.6% ✅ |
| MMLU | 50.6% | -2.3% ❌ |
| RepliQA | 34.1% | -6.4% ❌ |

---

## V2修正計画

### 仮説: サンプル数の違い

**元のSST-Merge**:
- aggregated_results.json: おそらくs=1000
- RepliQA 40.5%

**V2**:
- s=500
- RepliQA 34.1%

**対策**: s=1000で再実行

---

### 仮説: 実装の微妙な違い

**元のSST-Merge**:
```python
merged = alpha * utility + alpha * safety_projected
# alpha=1.0の場合
merged = utility + safety_projected
```

**V2**:
```python
merged = utility + safety_weight * safety_projected
# safety_weight=1.0の場合
merged = utility + safety_projected
```

**同じ公式だが、結果が異なる**

**可能性**:
1. FIM計算の精度の違い
2. 射影の実装の微妙な違い
3. データローダーの違い

---

### 推奨される修正計画

#### Phase 1: サンプル数の増加（最優先）

```bash
# s=1000で再実行
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 20 \
    --safety_weight 1.0 \
    --max_samples 1000 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k20_*_s1000_*.pt \
    --model llama-3.1-8b \
    --max_samples 500
```

**期待**:
- RepliQA: 34.1% → 38-40%
- MMLU: 50.6% → 52-53%
- Jailbreak: 78.2% → 77-78%

---

#### Phase 2: k=3-5のテスト

```bash
# k=3
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 3 \
    --safety_weight 1.0 \
    --max_samples 1000 \
    --use_fim

# k=5
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 5 \
    --safety_weight 1.0 \
    --max_samples 1000 \
    --use_fim
```

**期待**:
- k=3: Jailbreak 75-76%, MMLU 52%, RepliQA 40%
- k=5: Jailbreak 76-77%, MMLU 52%, RepliQA 40%

---

#### Phase 3: αの最適化

```bash
for alpha in 0.8 0.9 1.0; do
    python scripts/run_merge.py \
        --model llama-3.1-8b \
        --variant A5+A7 \
        --k 20 \
        --safety_weight $alpha \
        --max_samples 1000 \
        --use_fim
done
```

**期待**:
- α=0.9: RepliQA 31-33%
- α=1.0: RepliQA 38-40%

---

## まとめ

### 元のSST-Mergeの最良設定

1. **k=20, α=1.0**: Jailbreak 77.6%, MMLU 52.9%, RepliQA 40.5% ✅
2. **k=3, α=1.0**: Jailbreak 75.8%, MMLU 52.3%, RepliQA 40.5% ✅
3. **k=5, α=1.0**: RepliQA 40.5% ✅

### V2の問題

1. **RepliQAが低い**: 34.1% vs 40.5% (-6.4%)
2. **MMLUが低い**: 50.6% vs 52.9% (-2.3%)

### 根本原因の可能性

1. **サンプル数不足**: s=500 vs s=1000
2. **FIM計算の精度**: 実装の微妙な違い
3. **データローダーの違い**: RepliQAデータの処理方法

### 次のアクション

**今すぐ実行**:
```bash
# s=1000で再実行
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 20 --safety_weight 1.0 --max_samples 1000 --use_fim
```

**期待結果**: RepliQA 38-40%, MMLU 52-53%, Jailbreak 77-78%
