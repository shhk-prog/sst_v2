# Walkthrough - v3/scripts の整理

`v3/scripts` ディレクトリ内の 38 個のスクリプト群を目的・機能別にサブディレクトリへ整理・分類し、各種パイプラインからの呼び出しパスおよびドキュメント（`v3/README.md`）を更新しました。

---

## 完了した修正・変更点

### 1. サブディレクトリ構造の構築とファイルの整理・配置

以下の 6 つのサブディレクトリを作成し、該当するスクリプトを適切に分類・移動しました：

- **`v3/scripts/eval/`** (評価・ベンチマーク系)
  - [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_safety.py) (HarmBench / JailbreakBench 等の安全性評価)
  - [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py) (lm-evaluation-harness ユーティリティ評価)
  - [eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_alpaca.py) (AlpacaEval 2 評価)
  - [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_instruction_datasets.py) (Evol-Instruct / MedAlpaca 評価)
  - [eval_hirundo_unlearning.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_hirundo_unlearning.py) (Unlearning 指標評価)
  - [check_harmbench_results.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/check_harmbench_results.py) (HarmBench 結果チェック)

- **`v3/scripts/merging/`** (マージ手法・補助スコア計算系)
  - [compute_datafree_importance.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merging/compute_datafree_importance.py) (Data-Free SST 用の重み差分重要度計算)
  - [matena_fisher.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merging/matena_fisher.py) (MatEna Fisher 重み計算・マージ)
  - [prepare_led_scores.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merging/prepare_led_scores.py) (LED-Merging スコア準備)
  - [elect_led_masks.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merging/elect_led_masks.py) (LED-Merging マスク選定)

- **`v3/scripts/analysis/`** (解析・集計・視覚化系)
  - [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/pareto_auc.py) (Pareto Frontier AUC 解析およびプロット)
  - [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_tables.py) (Markdown/LaTeX テーブル自動生成)
  - [count_dataset_sizes.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/count_dataset_sizes.py) (データセット規模の確認・集計)

- **`v3/scripts/tools/`** (モデル・環境ツール系)
  - [create_dummy_models.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/tools/create_dummy_models.py) (テスト用軽量ダミーモデル生成)
  - [create_full_model.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/tools/create_full_model.py) (LoRA アダプタのマージ済み Full Model 変換)

- **`v3/scripts/tests/`** (テスト・動的検証フック系)
  - [steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/tests/steering_hook.py) (実験規約遵守チェック・動的フック)
  - [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/tests/test_steering_hook.py) (フック動的検証用ユニットテスト)
  - [test_merge_all.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/tests/test_merge_all.py) (全マージ手法の統合テスト)

- **`v3/scripts/fixes/`** (データ修正・修復ユーティリティ系)
  - [fix_all_alpaca_eval_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_all_alpaca_eval_jsons.py)
  - [fix_humaneval_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_humaneval_jsons.py)
  - [fix_ifeval_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_ifeval_jsons.py)
  - [fix_mbpp_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_mbpp_jsons.py)
  - [fix_mmlu_pro_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_mmlu_pro_jsons.py)
  - [clean_failed_results.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/clean_failed_results.py)
  - [clean_ifeval_results.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/clean_ifeval_results.py)
  - [verify_mbpp_fix.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/verify_mbpp_fix.py)

- **トップレベルに維持された主要ランナー**:
  - `run_experiments.py`, `merge.py`, `merge_eval_parallel.py`, `run_base_eval_parallel.py`, `run_mergekit_parallel.py`, `fine_tuning.py`, `data_prep.py`, `setup_env.sh`

---

### 2. スクリプト内の呼び出しパスの同期更新

トップレベルの自動化ランナースクリプトおよび各モジュール内のサブプロセス呼び出しパスを安全に更新しました：
- [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py): `scripts/eval/eval_*.py`, `scripts/analysis/pareto_auc.py` へ修正
- [merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py): `scripts/eval/eval_*.py` へ修正
- [run_base_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_base_eval_parallel.py): `scripts/eval/eval_*.py` へ修正
- [eval_hirundo_unlearning.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_hirundo_unlearning.py): `scripts/eval/eval_safety.py` および `scripts/eval/eval_utility.py`, `scripts/tests/steering_hook.py` へ修正
- [fix_ifeval_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_ifeval_jsons.py) / [fix_mmlu_pro_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_mmlu_pro_jsons.py): `scripts/eval/eval_utility.py` へ修正

---

### 3. ドキュメントの更新

- [v3/README.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/README.md): 全体のディレクトリツリー構造および最新のスクリプト解説を反映。

---

## ワンクリック・クリーンアップコマンド (推奨)

移動前の `v3/scripts/` 直下の旧ファイルを一括で削除するには、以下のターミナルコマンドを実行してください：

```bash
python3 -c '
import os
files = ["check_harmbench_results.py","clean_failed_results.py","clean_ifeval_results.py","compute_datafree_importance.py","count_dataset_sizes.py","create_dummy_models.py","create_full_model.py","elect_led_masks.py","eval_alpaca.py","eval_hirundo_unlearning.py","eval_instruction_datasets.py","eval_safety.py","eval_utility.py","fix_all_alpaca_eval_jsons.py","fix_humaneval_jsons.py","fix_ifeval_jsons.py","fix_mbpp_jsons.py","fix_mmlu_pro_jsons.py","generate_tables.py","matena_fisher.py","pareto_auc.py","prepare_led_scores.py","steering_hook.py","test_merge_all.py","test_steering_hook.py","verify_mbpp_fix.py",".DS_Store","._.DS_Store","._run_base_eval_parallel.py","._run_mergekit_parallel.py"]
for f in files:
    p = os.path.join("v3/scripts", f)
    if os.path.exists(p): os.remove(p)
print("Old script cleanup complete.")
'
```
