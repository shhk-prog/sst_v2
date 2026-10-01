# 修正内容の確認 (Walkthrough)

モデルマージ処理の実行時に発生していた `FileNotFoundError`（出力先ディレクトリ `models/merged` が存在しない問題）に対する修正内容をまとめます。

## 変更内容

### [uncertainty_based_gradient_matching.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/code/uncertainty_based_gradient_matching.py)

- `shutil.copy` によって事前学習済みモデルの補助ファイル（`merges.txt` など）を出力先ディレクトリ（`args.out_model_path`）にコピーする際、出力先ディレクトリが事前に作成されていないため `FileNotFoundError` が発生していました。
- これを解決するため、コピー処理を行うループの前に以下のコードを追加し、出力先ディレクトリが自動的に作成されるように修正しました。

```python
    if args.pretrained_model_name_or_path is not None:
        if os.path.exists(args.pretrained_model_name_or_path):
            if args.out_model_path is not None:
                os.makedirs(args.out_model_path, exist_ok=True)
            for file in os.listdir(args.pretrained_model_name_or_path):
```

## 検証結果

ユーザー様によりターミナル環境にて `./run_model_merging_pipeline.sh` が再実行され、エラーなくマージ処理および最終評価が正常に完了したことを確認しました。

### 再現実験結果サマリー (Accuracy)

| Task     | Expert (Single) | Merged (Ours)   | Diff       |
|----------|-----------------|-----------------|------------|
| imdb     | 0.944           | 0.869           | -0.075     |
| yelp     | 0.9694          | 0.9598          | -0.0096    |
| rt       | 0.87617         | 0.86023         | -0.01594   |
| sst2     | 0.93693         | 0.91514         | -0.02179   |
| amazon   | 0.953           | 0.9308          | -0.0222    |
