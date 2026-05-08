# マージ手法のα値実装検証レポート

**検証日**: 2026-02-03  
**目的**: 加算型とbaselineが同じかどうか、コードレベルで検証

---

## 🔍 検証結果

### 加算型とbaselineは**異なります**

**理由**: LoRAアダプターとフルモデルで実装が根本的に異なります。

---

## 📊 各手法の実装詳細

### 1. SST-Merge加算型（Additive）

**ファイル**: `sst_merge.py`  
**関数**: `SSTMerge._merge_with_mask()` (行521-626)

#### 実装式：
```python
# LoRAアダプターの加算型マージ
merged[i] = utility[i] + α × layer_weight × mask[i] × safety[i]
```

**コード抜粋**（行595）:
```python
# 加算型マージ: utility + weight * safety
# Utilityを完全に保持し、Safetyを高λ方向にのみ追加
merged[key] = utility_val + safety_weight * safety_val
```

**αの意味**:
- Safetyアダプターをどれだけ**加算**するか
- α=0: Utilityのみ
- α=0.5: Utility + Safety×0.5
- α=1.0: Utility + Safety（フル加算）

#### 特徴：
✅ **LoRAアダプター同士**のマージ  
✅ GEVPマスクでパラメータ選択  
✅ Utilityを完全保持

---

### 2. SST-Merge補間型（Interpolation）

**ファイル**: `sst_merge_interpolation.py`  
**関数**: `SSTMergeInterpolation._merge_with_mask_interpolation()` (行196-316)

#### 実装式：
```python
# 補間型マージ
merged[i] = (1 - α × layer_weight × mask[i]) × utility[i] 
          + (α × layer_weight × mask[i]) × safety[i]
```

**コード抜粋**（行281）:
```python
merged[key] = utility_weight * utility_val + safety_weight * safety_val
```

**αの意味**:
- SafetyとUtilityの間での**補間比率**
- α=0: 完全にUtility
- α=0.5: Utility 50% + Safety 50%
- α=1.0: 完全にSafety（マスク適用時）

#### 特徴：
✅ **LoRAアダプター同士**のマージ  
✅ GEVPマスクでパラメータ選択  
✅ Utility と Safety のブレンド

---

### 3. Baseline (Task Arithmetic, TIES, DARE)

**ファイル**: `baseline_merge.py`  
**関数**: `CustomBaselineMerger.task_arithmetic()` (行285-307)

#### 実装式：
```python
# Task Arithmetic: 重み付き平均
merged = Σ w_i × adapter_i
      = w_utility × Δθ_utility + w_safety × Δθ_safety
```

**コード抜粋**（行303）:
```python
weighted_sum += weight * adapter[key]
```

**αの意味**:
- **重み付き平均**での比率
- α=0.5: utility 50% + safety 50%（補間型と同じ）

#### 特徴：
✅ **LoRAアダプター同士**のマージ  
❌ GEVPマスクなし  
✅ シンプルな重み付き平均

---

## ⚠️ 重要な違い

### 加算型 vs Baseline

| 項目 | 加算型 | Baseline |
|------|--------|----------|
| **実装対象** | LoRAアダプター | LoRAアダプター |
| **基本式** | `U + α×S` | `w1×U + w2×S` |
| **α=0.5の意味** | U + 0.5×S | 0.5×U + 0.5×S |
| **Utility保持** | ✅ 100%保持 | ❌ 50%に減少 |
| **GEVP使用** | ✅ あり | ❌ なし |

**結論**: 加算型とbaselineは**完全に異なる**手法です！

### 補間型 vs Baseline

| 項目 | 補間型 | Baseline |
|------|--------|----------|
| **実装対象** | LoRAアダプター | LoRAアダプター |
| **基本式** | `(1-α)×U + α×S` | `w1×U + w2×S` |
| **α=0.5の意味** | 0.5×U + 0.5×S | 0.5×U + 0.5×S |
| **GEVP使用** | ✅ あり | ❌ なし |

**結論**: 補間型とbaselineは**αの意味が同じ**ですが、GEVPマスクの有無が異なります。

---

## 📈 α値での比較の妥当性

### ❌ 加算型 vs Baseline （同じα値は不適切）

```python
# 加算型 α=0.5
merged = utility + 0.5 × safety
# → Utility 100% + Safety 50% = 150%相当

# Baseline α=0.5
merged = 0.5 × utility + 0.5 × safety
# → Utility 50% + Safety 50% = 100%

# 完全に異なる！
```

**推奨**: 性能基準での比較（例: Jailbreak耐性90%を達成するα値を各手法で見つけて比較）

### ✅ 補間型 vs Baseline （同じα値は妥当）

```python
# 補間型 α=0.5
merged = 0.5 × utility + 0.5 × safety

# Baseline α=0.5
merged = 0.5 × utility + 0.5 × safety

# αの意味は同じ！
# ただし、GEVPマスクの効果を評価することになる
```

**推奨**: 同じα値での比較は妥当。GEVPマスクの効果を評価できます。

---

## 🎯 適切な比較方法

### 方法1: Pareto Frontier分析

Jailbreak耐性 vs Utility性能の散布図で評価：
- どの手法が最良のトレードオフを提供するか
- 全α範囲での性能曲線を比較

### 方法2: 等性能比較

同じUtility性能を維持した場合のJailbreak耐性で評価：
- 例: Utility ROUGE-1 = 60%を達成するα値を見つける
- その時のJailbreak耐性を比較

### 方法3: 分離分析

各手法を別々に分析：
- **加算型**: k値とGEVP/layerwiseの効果
- **補間型 vs Baseline**: GEVPマスクの効果
- **手法間**: Pareto frontierで比較

---

## ✅ 結論

1. **加算型 ≠ Baseline**: 完全に異なる手法。同じα値での比較は不適切。

2. **補間型 ≈ Baseline（αの意味）**: αの意味は同じだが、GEVP有無が異なる。同じα値での比較は妥当だが、GEVPマスクの効果を評価していることに注意。

3. **適切な比較**: 
   - 加算型: 独自に評価（Utility保持しながらSafety追加の効果）
   - 補間型 vs Baseline: 同じαで比較可能（GEVPマスクの効果評価）
   - 全体: Pareto frontier分析を推奨
