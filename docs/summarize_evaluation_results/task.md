# Task: 評価結果の集計とマージ方式別比較表の作成

## 目的
Seed42, Seed43, Seed44 の全評価データから、各ドメインパターン（`code+safety`, `math+safety`, `medical+safety`, `math+medical+code+safety`）および各 Merge 方式（`diagonal_sst_main`, `data_free_sst_main`, `ties`, `dare`, `della`, `task_arithmetic`, `safemerge`, `led_merging`, `matena_fisher`, `mergealign` 等）ごとの各評価指標（Safety, Math, Code, Medical, General/Instruction）の結果を集計し、比較表として作成・整理する。

## タスクリスト

- [x] 結果ディレクトリ構造および各指標の JSON スコアスキーマ確認 <!-- id: 0 -->
- [x] ドメインパターン別の評価メトリクス集計・表形式への整理 <!-- id: 1 -->
  - [x] Safety: HarmBench, JailbreakBench, StrongReject, WildJailbreak
  - [x] Math: GSM8K, Minerva Math500
  - [x] Code: HumanEval, MBPP
  - [x] Medical: PubMedQA, MedQA 4-options
  - [x] General / Instruction: MMLU, IFEval, AlpacaEval2, Evol-Code, MedAlpaca
- [x] walkthrough.md への詳細集計テーブルの記録・出力 <!-- id: 2 -->
- [x] ユーザーへの日本語結果報告の作成 <!-- id: 3 -->
