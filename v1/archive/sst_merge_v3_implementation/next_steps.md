# SST-Merge V3 評価後の次のステップ

## 現在の状況

- ✅ SST-Merge V3のマージ完了
- ✅ Layer-wise Projection適用成功（FFN: 0.3, Attention: 1.0, lm_head: 3.0）
- ✅ マージされたアダプター保存: `sst_v3_A5_A7_layerwise_w1.0_k5_20260107_020833.pt`
- 🔄 評価実行中（1時間20分経過）

## 評価完了後の手順

### 1. 結果の確認

評価スクリプトは結果を**標準出力に表示**します（ファイル保存なし）。

**確認する項目**:
```
Jailbreak Resistance: XX.XX% (500 samples)

Safety Metrics:
  Refusal Rate: XX.XX%
  Harmful Response Rate: XX.XX%
  (500 samples)

Utility Metrics:
  MMLU: XX.XX% (500 samples)
  RepliQA: XX.XX% (500 samples)
```

### 2. 結果の保存

ターミナル出力をファイルに保存：
```bash
# 評価完了後、ターミナル出力をコピーして保存
cat > sst_merge_v3/results/llama-3.1-8b/evaluation_results_20260107.txt << 'EOF'
[ターミナル出力をここに貼り付け]
EOF
```

### 3. 結果の分析

#### 目標との比較

| メトリクス | 目標 | V3結果 | 達成 |
|-----------|------|--------|------|
| Jailbreak | 90%+ | ? | ? |
| MMLU | 52%+ | ? | ? |
| RepliQA | 40%+ | ? | ? |

#### 元のSST-Mergeとの比較

| メトリクス | 元のSST (k=5) | V3 (Layer-wise) | 改善 |
|-----------|---------------|----------------|------|
| Jailbreak | 77.8% | ? | ? |
| MMLU | 49.6% | ? | ? |
| RepliQA | 33.7% | ? | ? |

### 4. Layer-wise Projection効果の分析

**分析ポイント**:
- FFN層（w=0.3）: Utility維持に貢献したか？
- Attention層（w=1.0）: バランスが取れているか？
- 出力層（w=3.0）: Jailbreak改善に貢献したか？

### 5. 追加実験（必要に応じて）

#### オプション1: Safety Weightの調整

現在のw=1.0で目標未達の場合：
```bash
# w=1.5で再実行
python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --k 5 --safety_weight 1.5 --max_samples 500 --use_fim
```

#### オプション2: 出力層のWeightを調整

`layer_config.py`を修正：
```python
LAYER_SAFETY_WEIGHTS = {
    'lm_head': 5.0,  # 3.0 → 5.0に増加
    # ...
}
```

### 6. 最終レポート作成

#### 作成するドキュメント

1. **`sst_merge_v3_final_report.md`**
   - V3の設計と実装
   - 評価結果
   - 元のSST-Mergeとの比較
   - Layer-wise Projectionの効果分析
   - 結論と今後の方向性

2. **`sst_merge_v3_results.json`**
   ```json
   {
     "method": "SST-Merge V3",
     "layer_wise_projection": {
       "ffn": 0.3,
       "attention": 1.0,
       "lm_head": 3.0
     },
     "results": {
       "jailbreak": 0.XX,
       "mmlu": 0.XX,
       "repliqa": 0.XX
     },
     "comparison": {
       "baseline": "Original SST-Merge (k=5)",
       "improvement": {
         "jailbreak": "+XX.X%",
         "mmlu": "+X.X%",
         "repliqa": "+X.X%"
       }
     }
   }
   ```

### 7. ドキュメントの整理

```bash
# docsディレクトリに保存
mkdir -p docs/sst_merge_v3_implementation
cp /mnt/iag-02/home/hiromi/.gemini/antigravity/brain/*/\*.md docs/sst_merge_v3_implementation/
cp sst_merge_v3/results/llama-3.1-8b/evaluation_results_20260107.txt docs/sst_merge_v3_implementation/
```

---

## 次のアクション（優先順位順）

1. ⏳ **評価完了を待つ**
2. 📊 **結果を確認・保存**
3. 📈 **結果を分析**
4. 📝 **最終レポート作成**
5. 📁 **ドキュメント整理**
6. ✅ **完了**

---

## 評価が完了したら

ターミナル出力を確認して、以下の情報を教えてください：
- Jailbreak Resistance: XX.XX%
- MMLU: XX.XX%
- RepliQA: XX.XX%

その後、結果の分析と最終レポートを作成します。
