# Data-Free SST-Merge: α値とJB耐性の関係分析

## 問題の概要

Data-Free SST-Mergeの評価結果において、α値の増加に対するJailbreak耐性の変化が不自然である。

### 観察された現象

#### A5_A7 (RepliQA)
| α | JB Resistance |
|---|---|
| 0.05 | 71.60% |
| 0.5 | 72.20% |
| 1.0 | 67.80% |

- α=0.05から1.0への増加で、JB耐性が**下降**（71.60% → 67.80%）
- 期待値: α増加 → JB耐性上昇

#### A6_A7 (Alpaca)
| α | JB Resistance |
|---|---|
| 0.05 | 80.40% |
| 0.5 | 80.60% |
| 1.0 | 81.40% |

- α=0.05から1.0への増加で、JB耐性が微増（80.40% → 81.40%）
- 変化が非常に小さい（約1%）

## マージ実装の確認

### アダプターペア構成
```python
merge_pairs = [
    # A5_A7: RepliQA (Utility) + Safety
    ("A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4",
     "A7_safety_meta_llama_3.1_8b_instruct_r16_7ep_lr2e-4",
     "A5_A7"),
     
    # A6_A7: Alpaca (Utility) + Safety
    ("A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_7ep_lr2e-4",
     "A7_safety_meta_llama_3.1_8b_instruct_r16_7ep_lr2e-4",
     "A6_A7"),
]
```

→ **両ペアとも同じSafetyアダプター（A7）を使用**

### マージ方式
`sst_merge_data_free.py` (271行目):
```python
merged_adapter[key] = u_param + (self.safety_weight * layer_weight) * param_mask * s_param
```

形式: **`merged = Utility + α × mask × Safety`** (加算型)

- `α` (safety_weight): ユーザー指定のSafety重み（0.05〜1.0）
- `mask` (param_mask): GEVPベースのマスク（0〜1の値）
- `layer_weight`: Layerwiseの層別重み（0.6〜1.0）

## 仮説：GEVPマスクがα値の効果を抑制

### GEVPマスクの計算
```python
λ_i = F_safety[i] / F_utility[i]
mask_i = sigmoid(λ_i - threshold)
```

- `λ`が大きい → Safety FIMが大きい → `mask ≈ 1`
- `λ`が小さい → Utility FIMが大きい → `mask ≈ 0`

### 問題の核心

**マスクがパラメータごとに固定**されているため：
1. Safety FIMが大きいパラメータ（`mask ≈ 1`）では、α値の変化が直接効く
2. Utility FIMが大きいパラメータ（`mask ≈ 0`）では、α値を変えてもほぼ効果なし

もし全体的に`mask`の値が低い（多くのパラメータでUtility FIMが優勢）場合、**α値を増やしても実質的な効果は限定的**になる。

### A5_A7とA6_A7の違い

#### A5_A7 (RepliQA)
- Utility FIMがSafety FIMより大きい領域が多い？
- → マスクが全体的に低い
- → α増加の効果が限定的、むしろUtilityタスクへの悪影響が大きくなる
- → JB耐性が横ばい〜微減

#### A6_A7 (Alpaca)
- Safety FIMとUtility FIMがよりバランスしている？
- → マスクが中程度の値
- → α増加の効果がやや出る（80.40% → 81.40%）

## 通常のSST-Merge（加算型）との比較

通常のSST-Merge（加算型）では、α値の増加に対してJB耐性が明確に上昇する傾向が見られる。

**主な違い:**
- **FIM計算方法**
  - 通常版: 実際の学習データでFIMを計算
  - Data-Free版: LoRA重みの二乗ノルムで近似（`FIM ≈ ||ΔW||²`）
  
- **FIM近似の正確性**
  - Data-Free版のFIM近似が不正確な場合、GEVPマスクも不正確になる
  - → α値の効果が期待通りに現れない

## 結論

### データフリー版の特性
1. **方式は加算型**: `merged = Utility + α × mask × Safety`
2. **α値の効果はGEVPマスクに依存**: マスクが低いと効果が限定的
3. **FIM近似の精度**: データフリー近似（`||ΔW||²`）の限界

### なぜA5_A7でJB耐性が横ばいなのか
- RepliQA utilityアダプター（A5）とSafetyアダプター（A7）のFIM分布が、GEVPマスクを低く設定している
- マスクが低い → α値を増やしてもSafetyの影響が少ない
- Utilityへの悪影響の方が大きくなる可能性

### なぜA6_A7では微増するのか
- Alpaca utilityアダプター（A6）とSafetyアダプター（A7）のFIM分布が、よりバランスしている
- マスクが中程度 → α値の増加がある程度効果を示す

## 推奨される検証

1. **FIM値の分布確認**
   - A5とA7のFIM分布を比較
   - A6とA7のFIM分布を比較
   - マスク値の実際の分布を確認

2. **GEVPなしマージの比較**
   - `use_gevp=False`でシンプルマージを実行
   - α値とJB耐性の関係を確認

3. **通常版SST-Mergeとの比較**
   - 同じペアで通常版（データあり）を実行
   - α値の効果の違いを比較
