# 整理計画: merged フォルダ内の結果整理および評価スクリプト出力先の変更

`/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged` フォルダの整理は完了しました。
続いて、評価実行時に出力される評価結果（JSONファイルおよび付随するディレクトリ）についても、同様に `seedXX/手法名/` フォルダの下に出力されるよう、以下のスクリプトを修正します。

## 対象スクリプト

1. **[run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)**
   - `run_merge_eval_phase` において、マージモデル評価時の `eval_model` 呼び出しで出力ディレクトリを `seed{seed}/{method}` に変更します。
2. **[merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)**
   - `eval_model_on_gpu` において、出力ファイルパスを `seed{seed}/{method}` のサブディレクトリ下に変更します。

## 提案する変更内容

### 評価スクリプト出力先の修正

#### [MODIFY] [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
- `eval_model` 関数に `output_dir` 引数を追加します（デフォルトは `RESULT_DIR`）。
- `run_merge_eval_phase` でシードおよびマージ手法（`re` を用いたパース）を特定し、`output_dir` として `{RESULT_DIR}/seed{seed}/{method}` を渡すようにします。

#### [MODIFY] [merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)
- `import re` を追加。
- `eval_model_on_gpu` 内で、`model_name` から `re` を用いて手法名を抽出します。
- `result_dir` (例: `results/debug_limit320/merged`) に `seed{seed}/{method}` を結合したディレクトリを作成し、そこへ結果を出力するように修正します。

## 検証計画

### 自動テスト / 動作確認
1. 修正したスクリプトを実行し、新しい評価結果が想定通りのフォルダ構成（`merged/seedXX/手法名/...`）で出力されるか確認します。
2. `resume` 機能（既存結果のスキップ）が正しく動作することを確認します。
