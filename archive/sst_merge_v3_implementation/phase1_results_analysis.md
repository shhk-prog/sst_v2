# Phase 1 評価結果分析

## 評価結果サマリー

### Phase 1 (k=10, 修正版SST-Merge)

```json
{
  "jailbreak_resistance": 74.8%,
  "refusal_rate": 3.0%,
  "harmful_rate": 0.8%,
  "mmlu_accuracy": 49.6%,
  "repliqa_rouge_l": 34.0%
}
```

---

## ベースラインとの比較

| メトリクス | Base Model | A5 (Utility) | A7 (Safety) | 元のSST (k=20) | **Phase 1 (k=10)** | 目標 |
|-----------|------------|--------------|-------------|----------------|-------------------|------|
| **Jailbreak** | 53.4% | 76.6% | 100% | 77.6% | **74.8%** | 77%+ |
| **MMLU** | 53.7% | 52.7% | 0% | 52.9% | **49.6%** | 52%+ |
| **RepliQA** | 10.9% | 40.2% | 1.3% | 40.5% | **34.0%** | 40%+ |
| **Refusal Rate** | 10.4% | 1.8% | 100% | 2.0% | **3.0%** | - |

---

## 問題点の分析

### 1. **全てのメトリクスで目標未達**

**Jailbreak Resistance**: 74.8% < 77%（目標）
- 元のSST-Merge (77.6%)より**低い**
- A5単体 (76.6%)より**低い**
- **問題**: Safetyが全く向上していない

**MMLU**: 49.6% < 52%（目標）
- 元のSST-Merge (52.9%)より**大幅に低い**
- A5単体 (52.7%)より**大幅に低い**
- **問題**: Utilityが破壊されている

**RepliQA**: 34.0% < 40%（目標）
- 元のSST-Merge (40.5%)より**低い**
- A5単体 (40.2%)より**低い**
- **問題**: Utilityが破壊されている

### 2. **元のSST-Mergeより悪化**

| メトリクス | 元のSST (k=20) | Phase 1 (k=10) | 差分 |
|-----------|----------------|----------------|------|
| Jailbreak | 77.6% | 74.8% | **-2.8%** ❌ |
| MMLU | 52.9% | 49.6% | **-3.3%** ❌ |
| RepliQA | 40.5% | 34.0% | **-6.5%** ❌ |

**結論**: Phase 1の修正は**逆効果**

### 3. **k=10が小さすぎる可能性**

元のSST-Mergeはk=20で実行されていました。
- k=10: Safety Subspaceの次元が低すぎる
- 結果: Safetyの重要な情報が失われている

---

## 根本原因の仮説

### 仮説1: k=10では不十分

**理論**:
```
k↑ → Safety Subspaceの次元↑ → Safety情報保持↑
k↓ → Safety Subspaceの次元↓ → Safety情報損失↑
```

**検証**:
- 元のSST-Merge: k=20 → Jailbreak 77.6%
- Phase 1: k=10 → Jailbreak 74.8%
- **仮説**: k=20に戻せば改善する可能性

### 仮説2: 射影が過度にSafetyを削減

**理論**:
```
Safety_projected = V_k @ (V_k^T @ Safety)
k小 → 射影による情報損失大
```

**問題**:
- k=10では、Safetyの90%以上の情報が失われている可能性
- 結果: Jailbreak Resistanceが向上しない

### 仮説3: Utilityも破壊されている

**MMLU 49.6%の問題**:
- A5単体: 52.7%
- Phase 1: 49.6%
- **差分**: -3.1%

**RepliQA 34.0%の問題**:
- A5単体: 40.2%
- Phase 1: 34.0%
- **差分**: -6.2%

**原因**:
- 射影されたSafetyがUtilityに干渉している
- k=10では、Utility直交サブスペースの選択が不正確

---

## 実装の検証

### 確認すべき点

1. **GEVP解決が正しいか**
   - 固有値の順序: 高λ → Safety重要、Utility非重要
   - Safety Subspace選択: 上位k個の固有ベクトル

2. **射影が正しいか**
   - 公式: `P = V_k @ V_k^T`
   - 実装: `_project_param`メソッド

3. **マージが正しいか**
   - 公式: `merged = utility + safety_weight * safety_projected`
   - 実装: `merge_utility_safety`メソッド

---

## 次のステップ

### Step 1: k=20で再実行

```bash
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
```

**期待結果**: 元のSST-Merge (k=20)と同等
- Jailbreak: 77%+
- MMLU: 52%+
- RepliQA: 40%+

### Step 2: kグリッドサーチ

```bash
for k in 30 50 100 200; do
    python scripts/run_merge.py \
        --model llama-3.1-8b \
        --variant A5+A7 \
        --k $k \
        --safety_weight 1.0 \
        --max_samples 500 \
        --use_fim
    
    python scripts/evaluate.py \
        --adapter results/llama-3.1-8b/sst_v2_A5_A7_*_k${k}_*.pt \
        --model llama-3.1-8b \
        --max_samples 500
done
```

**目標**: Jailbreak 85-95%, Utility維持

### Step 3: 実装の詳細検証

```bash
# GEVPの固有値を確認
cat results/llama-3.1-8b/sst_v2_A5_A7_*.json | jq '.config'

# ログを確認
grep "eigenvalue" /tmp/sst_merge_phase1_test_v2.log
```

---

## 結論

### 現状

❌ **Phase 1は失敗**
- Jailbreak: 74.8% < 77%（目標）
- MMLU: 49.6% < 52%（目標）
- RepliQA: 34.0% < 40%（目標）

### 原因

1. **k=10が小さすぎる**: Safety情報が失われている
2. **射影による情報損失**: Utilityも破壊されている
3. **元のSST-Mergeより悪化**: 修正が逆効果

### 対策

1. ✅ **k=20で再実行**: 元のSST-Mergeと同等の性能を確認
2. ✅ **kグリッドサーチ**: 最適なkを見つける（k=30, 50, 100, 200）
3. ✅ **実装検証**: GEVP、射影、マージの各ステップを確認

### 期待される改善

- k=20: Jailbreak 77%+, MMLU 52%+, RepliQA 40%+
- k=50-100: Jailbreak 85-90%, MMLU 52%+, RepliQA 38-42%
- k=200: Jailbreak 95%+, MMLU 50%+, RepliQA 35-40%
