# 評価結果集計・比較表作成計画 (Evaluation Summary Plan)

`sst_v2` v3 で実行された全468モデルの評価結果 JSON から、ドメインパターンおよび Merge 方式ごとの評価結果を集計・まとめ表として整理する。

## 対象パターンと指標構成

### ドメインパターン (Domain Patterns)
1. `safety+code`
2. `safety+math`
3. `safety+medical`
4. `safety+math+code+medical`

### 対象指標 (Evaluation Metrics)
- **Safety (ASR↓ %)**: HarmBench, JailbreakBench, StrongReject, WildJailbreak
- **Math (Accuracy/Verify↑ %)**: GSM8K, Minerva Math500
- **Code (pass@1↑ %)**: HumanEval, MBPP
- **Medical (Accuracy↑ %)**: PubMedQA, MedQA 4-options
- **General / Instruction (% / win rate)**: MMLU, IFEval, AlpacaEval2, Evol-Code, MedAlpaca

### Merge 方式 (Merge Methods)
- `diagonal_sst_main` (提案手法 Diagonal SST)
- `data_free_sst_main` (提案手法 Data-free SST)
- `ties` (TIES-Merging)
- `dare` (DARE)
- `della` (DELLA)
- `task_arithmetic` (Task Arithmetic)
- `safemerge` (SafeMerge)
- `led_merging` (LED Merging)
- `matena_fisher` (RegMean / Matena Fisher)
- `mergealign` (MergeAlign)

## 成果物
- `docs/summarize_evaluation_results/walkthrough.md` に全パターン・全手法のスコア一覧表を記録
- ユーザーにわかりやすいマークダウンテーブル形式で報告
