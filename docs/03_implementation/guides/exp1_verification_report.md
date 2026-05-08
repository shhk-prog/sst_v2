# 実験1（Safety Tax定量化）検証レポート

## 実行コマンド

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment exp1
```

## 実行日時

**2025-12-22 02:44:09**

## ✅ 実行結果

### 結果ファイル

**パス**: `results/exp1_safety_utility/exp1_results_20251222_024409.json`

### 結果データ

```json
{
  "safety": {
    "refusal_rate": 0.014,
    "jailbreak_resistance": 0.986,
    "total_samples": 2000
  },
  "utility": {
    "accuracy": 0.7002563737359351,
    "total_samples": 14042
  },
  "safety_tax": 0.0,
  "baseline_safety": 0.7,
  "baseline_utility": 0.9
}
```

## 📊 詳細分析

### 1. データセット規模

| データセット | サンプル数 | 状態 |
|------------|----------|------|
| **BeaverTails（安全性）** | **2,000** | ✅ **実データ使用** |
| **MMLU（ユーティリティ）** | **14,042** | ✅ **実データ使用** |

**評価**: ✅ **大規模実データで評価済み**（ダミーデータではない）

### 2. SST-Mergeの動作確認

#### GEVP解法

```
2025-12-22 00:32:20,162 - src.gevp_solver - INFO - GEVP solved: 10 eigenvalues computed
2025-12-22 00:32:20,162 - src.gevp_solver - INFO - Top 5 safety efficiencies (λ): 
  [11338813.0, 9295677.0, 8076957.0, 7855354.5, 7624837.5]
```

**評価**: ✅ **GEVP解法が動作**
- 10個の固有値を計算
- 安全効率（λ）が計算された
- フォールバック（標準固有値分解）が正常に動作

#### Safety Subspace選択

```
2025-12-22 00:32:20,162 - src.gevp_solver - INFO - Safety subspace selected: dimension=10
```

**評価**: ✅ **安全サブスペース選択が動作**

### 3. 評価メトリクス

#### Safety Score

| メトリクス | 値 | 評価 |
|-----------|-----|------|
| **Refusal Rate** | **0.014** | ❌ **非常に低い** |
| Jailbreak Resistance | 0.986 | ✅ 高い |
| Total Samples | 2,000 | ✅ 十分 |

**問題点**: 
- **Refusal Rate（拒否率）が1.4%と非常に低い**
- 期待値: 70-90%
- 実際: 1.4%

**原因の可能性**:
1. モデルがほとんど拒否していない
2. 評価ロジックに問題がある可能性
3. プロンプトフォーマットの問題

#### Utility Score

| メトリクス | 値 | 評価 |
|-----------|-----|------|
| **Accuracy** | **0.7002** | ✅ **良好** |
| Total Samples | 14,042 | ✅ 十分 |

**評価**: ✅ **70%の精度は妥当**

#### Safety Tax

| メトリクス | 値 | 評価 |
|-----------|-----|------|
| **Safety Tax** | **0.0** | ⚠️ **計算されていない** |

**原因**: 
```python
safety_tax = 0.0  # 固定値
```

Safety Taxが計算されていない（常に0.0）

## ⚠️ 発見された問題

### 問題1: Safety Score（Refusal Rate）が異常に低い

**期待値**: 0.70-0.90  
**実際**: 0.014

**影響**: 安全性評価が正しく機能していない可能性

### 問題2: Safety Taxが計算されていない

**期待される計算**:
```python
utility_loss = baseline_utility - merged_utility
safety_gain = merged_safety - baseline_safety
safety_tax = utility_loss / safety_gain
```

**実際**: 常に0.0

**影響**: Safety Taxの定量化ができていない

### 問題3: GEVPがフォールバックしている

```
2025-12-22 00:32:20,016 - src.gevp_solver - ERROR - GEVP solving failed: 
  The leading minor of order 1806 of B is not positive definite.
2025-12-22 00:32:20,016 - src.gevp_solver - WARNING - Falling back to standard eigenvalue decomposition
```

**原因**: F_benignが正定値でない

**影響**: 
- GEVP解法の理論的優位性が発揮されていない
- 標準固有値分解にフォールバック

## ✅ 正常に動作している部分

### 1. データロード

- ✅ BeaverTails: 2,000サンプル
- ✅ MMLU: 14,042サンプル
- ✅ 実データで評価

### 2. SST-Mergeパイプライン

- ✅ FIM計算
- ✅ GEVP解法（フォールバック含む）
- ✅ サブスペース選択
- ✅ LoRAマージング

### 3. ユーティリティ評価

- ✅ MMLU精度: 70.02%
- ✅ 14,042サンプルで評価

## 📋 総合評価

| 項目 | 状態 | 評価 |
|------|------|------|
| **データセット** | 実データ使用 | ✅ **合格** |
| **サンプル数** | 2,000 + 14,042 | ✅ **合格** |
| **SST-Merge動作** | GEVP解法動作 | ✅ **合格** |
| **Utility評価** | 70.02%精度 | ✅ **合格** |
| **Safety評価** | 1.4%拒否率 | ❌ **不合格** |
| **Safety Tax計算** | 常に0.0 | ❌ **不合格** |
| **GEVP安定性** | フォールバック | ⚠️ **要改善** |

**総合**: ⚠️ **部分的に成功**

## 🔧 推奨される修正

### 修正1: Safety評価ロジックの確認

```python
# src/evaluation/safety_evaluator.pyを確認
# refusal_rateの計算ロジックを検証
```

### 修正2: Safety Tax計算の実装

```python
# experiments/run_real_experiments.pyで
utility_loss = max(0, baseline_utility - utility_score)
safety_gain = max(0, safety_score - baseline_safety)
safety_tax = utility_loss / safety_gain if safety_gain > 0 else 0.0
```

### 修正3: GEVP安定性の改善

```python
# src/gevp_solver.pyで
# F_benignに正則化を追加
F_benign = F_benign + 1e-6 * torch.eye(F_benign.shape[0])
```

## 結論

### ✅ 成功した点

1. **実データでの評価**: BeaverTails 2,000 + MMLU 14,042サンプル
2. **SST-Mergeの動作**: GEVP解法、サブスペース選択が動作
3. **ユーティリティ評価**: 70%の精度で妥当

### ❌ 改善が必要な点

1. **Safety評価**: Refusal Rateが1.4%と異常に低い
2. **Safety Tax**: 計算されていない（常に0.0）
3. **GEVP安定性**: フォールバックが発生

### 次のステップ

1. Safety評価ロジックの修正
2. Safety Tax計算の実装
3. GEVP安定性の改善
4. 修正後に再実行

**実験1は部分的に成功しましたが、Safety評価とSafety Tax計算に問題があります。**
