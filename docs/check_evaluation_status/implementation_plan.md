# 評価完了状態の検証計画 (Evaluation Status Check Plan)

v3 における全マージモデルの並列評価タスク（468モデル）が漏れなく完了しているかを検証・確認する。

## 調査対象と検証アプローチ

### 1. Slurm ジョブ実行ログの全数チェック
- `v3/logs/slurm_merge_101315/` 配下の `eval_model_0.log` 〜 `eval_model_467.log` (全468ファイル) を走査。
- `[DONE]` メッセージの有無、エラー・例外ログ (`Traceback`, `Error`, `OutOfMemory`, `failed`) の存在有無を点検。

### 2. 評価サマリー JSON のチェック
- `results/debug_limit320/merged/merge_eval_parallel_seeds42_summary.json`
- `results/debug_limit320/merged/merge_eval_parallel_seeds42-43-44_summary.json`
- 上記における `failed` 配列のエントリを確認。

### 3. ベンチマーク結果 JSON の生成状態チェック
- `results/debug_limit320/merged/seed42`, `seed43`, `seed44` 配下の各モデルフォルダに 15 種類の評価結果 JSON (`harmbench_safety`, `jailbreakbench_safety`, `strongreject_safety`, `wildjailbreak_safety`, `utility_math_gsm8k`, `utility_math_minerva_math500`, `utility_code_humaneval`, `utility_code_mbpp`, `utility_medical_pubmedqa`, `utility_medical_medqa_4options`, `utility_general_mmlu`, `utility_general_ifeval`, `alpaca_eval2`, `inst_evol_code`, `inst_medalpaca`) が正しく生成されているかをサンプルおよび全体構造から点検。

## 変更対象ファイル
なし (検証・確認作業のため)
