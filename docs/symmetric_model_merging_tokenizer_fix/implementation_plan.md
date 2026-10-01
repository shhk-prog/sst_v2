# 対称マージにおけるトークナイザー保存バグの修正計画

ベースモデルを `roberta-base`（HuggingFaceリポジトリ）に設定した際、Tokenizer 関連ファイルがローカルの `models/merged` にコピー・保存されないため、その後の評価処理（`predict.py`）でロードエラー（`OSError: Can't load tokenizer`）が発生する問題を修正します。

## ユーザーレビューが必要な事項
ありません。

## 未解決の質問
ありません。

## 提案される変更

### [Component: Model Merging]

#### [MODIFY] [uncertainty_based_gradient_matching.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/code/uncertainty_based_gradient_matching.py)
- HuggingFace の `AutoTokenizer` をインポートし、マージモデル保存時にベースモデル（`roberta-base` 等）から Tokenizer を自動ロードして `args.out_model_path` に保存する処理を追加します。

## 検証計画

### 手動確認
1. 古い評価ログや `models/merged` を削除します。
2. `./run_model_merging_pipeline.sh` を実行します。
3. `models/merged` ディレクトリ内に Tokenizer 関連ファイル（`vocab.json`, `merges.txt`, `tokenizer.json` 等）が保存され、評価スクリプトがエラーなく正常に走りきることを確認します。
