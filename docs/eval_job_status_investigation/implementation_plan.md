# 評価スキップ問題の修正計画 (Implementation Plan)

## 概要
ユーザーからの指摘に基づき、モデル評価スクリプトで評価結果が正しくスキップされずに再実行されてしまっていた以下の 2 つのバグを修正します。

1. **AlpacaEval2 (`eval_alpaca.py`) の `NameError: name 'generate_batch' is not defined` エラーの解消**
2. **MMLU (`eval_utility.py` および `merge_eval_parallel.py`) のタイムスタンプ付き結果ファイルによるスキップ失敗問題の解消**

---

## ユーザー確認事項
- 今回の変更は既存の推論・評価結果データに悪影響を与えず、過去にタイムスタンプ付きで出力されていた MMLU の結果ファイルを正規の `*_mmlu.json` に統合・自動検知できるようにします。

---

## 変更内容

### Component: `v3/scripts/eval/eval_alpaca.py`
#### [MODIFY] [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_alpaca.py)
- バッチ評価用の `generate_batch(model, tokenizer, items)` 関数を実装します。
- レフトパディングおよび `tokenizer.decode` によるテキスト生成を行い、Missing インデックスに対する推論を正常完了させます。

### Component: `v3/scripts/eval/eval_utility.py`
#### [MODIFY] [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
- `lm-eval` CLI フォールバックが `*_mmlu_<TIMESTAMP>.json` として出力した場合に、最新のタイムスタンプファイルを検出して本来の `output_file` (`*_mmlu.json`) に保存・統合する処理を追加します。
- 既存のタイムスタンプ付きファイルが存在する場合も検知して読み込めるようにします。

### Component: `v3/scripts/merge_eval_parallel.py`
#### [MODIFY] [merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)
- `output_complete()` 関数にて、`output_path` に直接アクセスできなかった場合でもタイムスタンプ付きファイル (`*_*.json`) を探索し、完了状態を正しく検出してスキップ判定できるように拡張します。

---

## 検証計画

### 自動/単体確認
- `python scripts/eval/eval_alpaca.py --help` や構文エラーチェック
- `merge_eval_parallel.py --config configs/config_main.yaml --seeds 42 43 44 --limit 320 --model_index 199 --resume` を実行し、モデル 199 番の MMLU が `skip complete` になることを確認
