# Task: IFEval実装コードの妥当性検証

## 目的
コードベースにおける IFEval (Instruction Following Evaluation) の実装・評価後処理ロジックが正しく実装されているかを検証し、レポートする。

## 確認対象コード
- `v3/scripts/eval/eval_utility.py`
  - `fix_ifeval_responses` 関数
  - `run_lm_eval_python_api` 関数
- `v3/scripts/merge_eval_parallel.py`
- `v3/results/debug_limit320/.../ifeval.json`（出力フォーマットおよびサンプルの整合性確認）

## ステータス
- [x] IFEval の設定および `lm-eval` 呼び出しロジックの確認
- [x] IFEval の結果後処理 (`fix_ifeval_responses`) のロジック精査
- [x] 指標（Prompt Strict/Loose Acc, Inst Strict/Loose Acc）の算出ロジックと標準仕様との比較
- [x] 報告用ドキュメントの作成
