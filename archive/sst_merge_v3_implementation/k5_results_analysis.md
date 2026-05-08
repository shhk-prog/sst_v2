# k=5 評価結果分析

## 結果サマリー

| メトリクス | k=5 (V2) | 目標 | 元のSST (k=5) | 差分 | 達成 |
|-----------|----------|------|---------------|------|------|
| Jailbreak | 76.00% | 77%+ | 77.8% | -1.8% | ❌ |
| MMLU | **52.20%** | 52%+ | ? | ? | ✅ |
| RepliQA | 33.66% | 40%+ | 40.5% | **-6.84%** | ❌ |
| Alpaca | 34.11% | - | - | - | - |

---

## 重要な発見

### 1. MMLUは目標達成

**MMLU: 52.20% > 52%** ✅
- k=20 (50.6%) → k=5 (52.2%) (+1.6%)
- **目標達成**

### 2. Jailbreakが目標未達

**Jailbreak: 76.00% < 77%** ❌
- 元のSST (k=5): 77.8%
- V2 (k=5): 76.0%
- **差分: -1.8%**

### 3. RepliQAが依然として低い

**RepliQA: 33.66% < 40%** ❌
- 元のSST (k=5): 40.5%
- V2 (k=5): 33.66%
- **差分: -6.84%**

---

## 問題の特定

### k=5でも改善しない理由

**期待**:
- k=5 → RepliQA 40.5%

**現実**:
- k=5 → RepliQA 33.66%

**原因**: **Residual Ratio = 0.7**

---

## Residual Ratioの影響

### 現在の実装

```
Mode: residual
Residual ratio: 0.7
```

**マージ公式**:
```python
blended_safety = (1 - 0.7) * safety_projected + 0.7 * safety_original
              = 0.3 * safety_projected + 0.7 * safety_original
merged = utility + blended_safety
```

**問題**:
- 70%が**射影されていない元のSafety**
- 元のSafetyは**Utility直交ではない**
- **Utilityを破壊** → RepliQA -6.84%

---

## 元のSST-Mergeとの比較

### 元のSST-Merge

```python
merged = utility + safety_projected
```

- 射影済みSafetyのみ使用
- Residual Ratio: 0（射影のみ）

### V2

```python
merged = utility + (0.3 * safety_projected + 0.7 * safety_original)
```

- Residual Ratio: 0.7
- 70%が元のSafety

---

## 修正計画

### 修正1: Residual Ratioを0に設定

**目的**: 元のSST-Mergeと同じ実装

**方法**: `run_merge.py`に`--residual_ratio`引数を追加

**実行**:
```bash
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 5 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim \
    --residual_ratio 0.0
```

**期待結果**:
- Jailbreak: 77-78% ✓
- MMLU: 52-53% ✓
- RepliQA: 40-41% ✓

---

### 修正2: modeをdirectに変更

**目的**: 射影を完全にスキップ

**実行**:
```bash
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 5 \
    --safety_weight 1.0 \
    --mode direct
```

**期待結果**:
- 元のSST-Mergeと同じ

---

## 結論

### 根本原因

**Residual Ratio = 0.7が問題**

- 元のSST-Merge: Residual Ratio = 0（射影のみ）
- V2: Residual Ratio = 0.7（70%が元のSafety）

### 解決策

**Residual Ratioを0に設定**

### 次のアクション

**今すぐ実行**:
```bash
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 5 --safety_weight 1.0 --max_samples 500 --use_fim --residual_ratio 0.0
```

**実行時間**: 約10分（FIM計算済みの場合）
