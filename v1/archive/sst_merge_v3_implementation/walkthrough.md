# SST-Merge V3 最終評価レポート（修正版）

## 評価結果サマリー

**評価日時**: 2026-01-07 04:13  
**モデル**: Llama-3.1-8B  
**設定**: k=5, safety_weight=1.0, Layer-wise Projection

### メトリクス（修正版）

| メトリクス | V3結果 | 元のSST (k=5) | 目標 | 達成 | 変化 |
|-----------|--------|---------------|------|------|------|
| **Jailbreak Resistance** | **80.2%** | 77.8% | 90%+ | ❌ | **+2.4%** ✅ |
| **MMLU** | **49.6%** | 49.6% | 52%+ | ❌ | **±0%** |
| **RepliQA (ROUGE-L)** | **33.78%** | 33.7% | 40%+ | ❌ | **+0.08%** |
| **Refusal Rate** | **1.8%** | - | - | - | - |

**重要**: 最初の抽出で11.11%と報告したRepliQAは、1つのサンプルのスコアでした。正しい結果は**33.78%**です。

---

## 詳細分析

### 1. Jailbreak Resistance: 80.2%

**結果**: 元のSST-Merge (77.8%) から **+2.4%の改善** ✅

**分析**:
- ✅ Layer-wise Projectionによる改善効果を確認
- ❌ 目標90%には届かず（-9.8%）
- 出力層（lm_head）のw=3.0では不十分

**評価**:
- 改善方向は正しい
- パラメータ調整で更なる改善が期待できる

### 2. MMLU: 49.6%

**結果**: 元のSST-Merge (49.6%) から **変化なし**

**分析**:
- ✅ Utilityは完全に維持された
- FFN層のw=0.3が適切に機能

### 3. RepliQA (ROUGE-L): 33.78%

**結果**: 元のSST-Merge (33.7%) から **+0.08%**（ほぼ変化なし）

**分析**:
- ✅ Utilityは維持された
- FFN層のw=0.3が適切に機能
- 目標40%には届かず

### 4. Refusal Rate: 1.8%

**結果**: 非常に低い

**分析**:
- モデルがほとんど拒否していない
- Jailbreak Resistance 80.2%と矛盾しない（拒否以外の方法で安全性を確保）

---

## Layer-wise Projection効果の分析

### 設定

| 層 | Safety Weight | 意図 | 結果 |
|----|---------------|------|------|
| lm_head | 3.0 | 出力層で強いSafety | Jailbreak +2.4% ✅ |
| Attention | 1.0 | 中程度 | - |
| FFN | 0.3 | Utility優先 | MMLU/RepliQA維持 ✅ |

### 効果

1. **出力層（w=3.0）**: 
   - Jailbreak +2.4%の改善
   - 効果はあるが不十分（目標-9.8%）

2. **FFN層（w=0.3）**:
   - MMLU維持（49.6%）✅
   - RepliQA維持（33.78%）✅
   - Utility優先の設計が正しく機能

3. **全体**:
   - Layer-wise Projectionの効果は確認できた
   - しかし、改善幅は限定的（+2.4%）

---

## 結論

### 成果

✅ **Layer-wise Projectionの実装成功**
- FFN層、Attention層、出力層に異なるWeightを適用
- Jailbreak +2.4%の改善を確認
- Utility完全維持（MMLU/RepliQA）

✅ **設計の妥当性確認**
- FFN層w=0.3: Utility維持に成功
- 出力層w=3.0: Jailbreak改善に貢献

### 課題

❌ **目標未達成**
- Jailbreak 80.2%（目標90%、-9.8%）
- MMLU 49.6%（目標52%、-2.4%）
- RepliQA 33.78%（目標40%、-6.22%）

❌ **改善幅が限定的**
- Jailbreak +2.4%のみ
- MMLU/RepliQAは変化なし

### 原因分析

1. **出力層のWeightが不十分**
   - w=3.0では目標に届かない
   - w=10.0～20.0が必要な可能性

2. **Base safety_weightが低い**
   - w=1.0では全体的な効果が弱い
   - w=2.0～3.0が必要な可能性

3. **Layer-wise Projectionの限界**
   - 層ごとのWeightだけでは大幅な改善は難しい
   - 他の手法との組み合わせが必要な可能性

---

## 次のステップ

### 優先度1: パラメータ調整

#### オプション1: 出力層のWeight大幅増加

`layer_config.py`を修正：
```python
LAYER_SAFETY_WEIGHTS = {
    'lm_head': 20.0,  # 3.0 → 20.0
    'q_proj': 1.0,
    'k_proj': 1.0,
    'v_proj': 1.0,
    'o_proj': 1.0,
    'gate_proj': 0.3,
    'up_proj': 0.3,
    'down_proj': 0.3,
}
```

#### オプション2: Base Safety Weight増加

```bash
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 5 --safety_weight 3.0 --max_samples 500 --use_fim
```

#### オプション3: 両方を組み合わせ

- 出力層: w=10.0
- Base: safety_weight=2.0

### 優先度2: 他の手法との組み合わせ

- **Residual Connection**: V2のresidual_ratioと組み合わせ
- **Adaptive Weighting**: データセットごとに動的にWeightを調整
- **Multi-stage Projection**: 複数段階でProjectionを適用

### 優先度3: 詳細な分析

- 各層のパラメータ変化を可視化
- Jailbreakサンプルの詳細分析
- Layer-wise Projectionの理論的限界を検討

---

## 比較表

### 元のSST-Merge vs V3

| メトリクス | 元のSST | V3 | 変化 | 評価 |
|-----------|---------|----|----|------|
| Jailbreak | 77.8% | 80.2% | +2.4% | ✅ 改善 |
| MMLU | 49.6% | 49.6% | ±0% | ✅ 維持 |
| RepliQA | 33.7% | 33.78% | +0.08% | ✅ 維持 |

### V3 vs 目標

| メトリクス | V3 | 目標 | 差分 | 評価 |
|-----------|----|----|------|------|
| Jailbreak | 80.2% | 90%+ | -9.8% | ❌ 未達 |
| MMLU | 49.6% | 52%+ | -2.4% | ❌ 未達 |
| RepliQA | 33.78% | 40%+ | -6.22% | ❌ 未達 |

---

## ファイル

- **マージ済みアダプター**: `sst_merge_v3/results/llama-3.1-8b/sst_v3_A5_A7_layerwise_w1.0_k5_20260107_020833.pt`
- **評価結果**: `sst_merge_v3/results/llama-3.1-8b/sst_v3_A5_A7_layerwise_w1.0_k5_20260107_020833.eval.json`
- **ドキュメント**: `docs/sst_merge_v3_implementation/`

---

## 推奨アクション

1. **パラメータ調整を試す**（出力層w=20.0、base w=3.0）
2. **結果を分析**
3. **目標達成できない場合、他の手法を検討**
