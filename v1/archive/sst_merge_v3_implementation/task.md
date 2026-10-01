# SST-Merge V3 実装タスク

## ✅ 完了したフェーズ

### Phase 1-4: 基本修正からV3実装まで
- [x] 元のSST-Mergeから新しくコピー
- [x] Layer-wise Projection実装（FFN 0.3, Attention 1.0, lm_head 3.0）
- [x] k=5, w=1.0でマージ実行成功
- [x] 評価実行完了

## 📊 評価結果

| メトリクス | V3結果 | 元のSST (k=5) | 目標 | 達成 |
|-----------|--------|---------------|------|------|
| Jailbreak | 80.20% | 77.8% | 90%+ | ❌ (+2.4%) |
| MMLU | 49.60% | 49.6% | 52%+ | ❌ (±0%) |
| RepliQA | 11.11% | 33.7% | 40%+ | ❌ (-22.59%) |

## ⚠️ 問題点

1. **Jailbreak 80.2%**: 目標90%に届かず（-9.8%）
   - 出力層w=3.0では不十分
   - Base safety_weight=1.0が低い

2. **RepliQA 11.11%**: 異常な低下（-22.59%）
   - 評価方法の問題の可能性が高い
   - FFN層w=0.3が低すぎる可能性

## 🔍 次のアクション

### 優先度1: RepliQA評価の検証
- [ ] 評価スクリプトを確認
- [ ] 元のSST-Mergeで再評価して比較

### 優先度2: パラメータ調整
- [ ] 出力層: w=10.0に増加
- [ ] FFN層: w=0.5に増加
- [ ] Base: safety_weight=2.0に増加
- [ ] 再マージ・再評価

## 📁 保存済みファイル

- **マージ済みアダプター**: `sst_merge_v3/results/llama-3.1-8b/sst_v3_A5_A7_layerwise_w1.0_k5_20260107_020833.pt`
- **評価結果**: `sst_merge_v3/results/llama-3.1-8b/sst_v3_A5_A7_layerwise_w1.0_k5_20260107_020833.eval.json`
- **ドキュメント**: `docs/sst_merge_v3_implementation/`
