# モデルマージ処理時の出力ディレクトリ未存在によるエラーの修正計画

モデルマージの実行スクリプト `uncertainty_based_gradient_matching.py` において、出力先ディレクトリ（`models/merged`）が存在しない状態で `shutil.copy` が呼び出され、`FileNotFoundError` が発生する問題を修正します。

## ユーザーレビューが必要な事項
ありません。

## 未解決の質問
ありません。

## 提案される変更

### [Component: Model Merging]
モデルマージ実行スクリプト `uncertainty_based_gradient_matching.py` を修正し、コピー処理を行う前に出力先ディレクトリを自動作成するようにします。

#### [MODIFY] [uncertainty_based_gradient_matching.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/code/uncertainty_based_gradient_matching.py)
- `shutil.copy` を実行する前に、`args.out_model_path` ディレクトリを作成する処理を追加します。

```python
    if args.out_model_path is not None:
        os.makedirs(args.out_model_path, exist_ok=True)
```

## 検証計画

### 手動確認
1. パイプライン実行スクリプト `./run_model_merging_pipeline.sh` を実行します。
2. `logs/merge.log` にエラーが出力されず、正常にマージ処理が完了することを確認します。
3. `models/merged` にマージされたモデルが正しく保存されていることを確認します。
4. パイプラインが最後まで走り、結果の集計サマリーテーブルが表示されることを確認します。
