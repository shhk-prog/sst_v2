# 修正内容の確認 (Walkthrough)

基準モデルを HuggingFace リポジトリ名（`roberta-base`）に設定した際、Tokenizer がマージモデルの出力先に保存されず、評価時に OSError が発生していたバグを修正しました。

## 変更内容

### [uncertainty_based_gradient_matching.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/code/uncertainty_based_gradient_matching.py)
- HuggingFace の `AutoTokenizer` をインポートし、マージ完了後（`new_model.save_pretrained` の後）に `args.pretrained_model_name_or_path` から Tokenizer をロードし、`args.out_model_path` (値は `models/merged`) に保存するコードを追加しました。

```python
    new_model.save_pretrained(args.out_model_path)
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.pretrained_model_name_or_path)
        tokenizer.save_pretrained(args.out_model_path)
    except Exception as e:
        print(f"Warning: Could not save tokenizer: {e}")
```

---

## 検証結果

再実行により、すべての評価スクリプトがエラーなく正常に完了し、モデルマージ後の精度サマリーが正しく出力されました。

### 対称マージ実験結果サマリー (Accuracy)

| タスク | Expert (単体) | Merged (前回の非対称) | Merged (今回の対称) | 性能変化 (前比) |
|--------|---------------|-----------------------|---------------------|-----------------|
| **imdb**   | 0.944         | 0.8690                | **0.9332**          | **+0.0642** (+6.42%p) |
| **yelp**   | 0.9694        | 0.9598                | **0.9614**          | **+0.0016** (+0.16%p) |
| **rt**     | 0.87617       | 0.86023               | **0.87054**         | **+0.0103** (+1.03%p) |
| **sst2**   | 0.93693       | 0.91514               | **0.92087**         | **+0.0057** (+0.57%p) |
| **amazon** | 0.953         | 0.9308                | **0.9452**          | **+0.0144** (+1.44%p) |
| **平均**   | 0.93590       | 0.90699               | **0.92624**         | **+0.01925** (+1.93%p) |
