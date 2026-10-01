# 実装計画: 16個のベンチマーク評価正当性の調査と検証

指定された16個のベンチマーク（Safety系 4種、Code系 2種、General系 3種、Math系 2種、Medical系 2種、Instruction系 3種）が、`sst_v2`（特に `v3` パイプライン）で正しく評価されているかを調査・検証します。

## 調査対象ベンチマーク一覧

| カテゴリ | ベンチマーク名 | 目的 |
| :--- | :--- | :--- |
| **Safety** | `harmbench` | CAIS HarmBench 分類器を用いた脱獄成功率 (ASR) 評価 |
| | `jailbreakbench` | JailbreakBench データセットに対する ASR 評価 |
| | `strongreject` | StrongREJECT 評価指標 (Score/ASR) 評価 |
| | `wildjailbreak` | WildJailbreak データセットに対する ASR 評価 |
| **Utility (Code)** | `code_humaneval` | HumanEval pass@1 精度評価 |
| | `code_mbpp` | MBPP (Sanitized含む) pass@1 精度評価 |
| **Utility (General)** | `general_ifeval` | IFEval 指示従順性 (Strict/Loose Pass Rate) 評価 |
| | `general_mmlu_pro` | MMLU-Pro 選択式精度評価 |
| | `general_mmlu` | MMLU 5-shot / 0-shot 選択式精度評価 |
| **Utility (Math)** | `math_gsm8k` | GSM8K 数学文章題精度評価 |
| | `math_minerva_math500` | MATH500 数学問題精度評価 |
| **Utility (Medical)** | `medical_medqa_4options` | MedQA (USMLE 4択) 選択式精度評価 |
| | `medical_pubmedqa` | PubMedQA 論文Q&A選択式精度評価 |
| **Instruction / FT Domain** | `inst_evol_code` | Evol-Instruct Code ドメイン評価 |
| | `inst_medalpaca` | MedAlpaca 医療ドメイン指示評価 |
| | `alpaca_eval2` | AlpacaEval 2.0 (LLM-as-a-Judge Win Rate / LC Win Rate) 評価 |

---

## 調査方針・アプローチ

1. **設定とパイプラインコードの点検 (`v3/scripts`, `v3/evaluators`)**:
   - 各ベンチマークの定義（データセットパス、プロンプトフォーマット、メトリクス計算式）がコード上で正しく構成されているか確認。
   - `lm_eval` のタスク名マッピングや `alpaca_eval` / `strong_reject` などのジャッジモデル呼び出しが適切か確認。

2. **過去の修正履歴・調査レポートの精査 (`docs/*`)**:
   - 既存の `docs/eval_*_investigation` や `docs/code_mbpp_evaluation_audit` 等のドキュメントを確認し、過去報告された不具合（例: MBPPのコード安全実行フィルタ、IFEvalのモデル出力パース、AlpacaEvalのAPI/Annotatorエラー等）が解決・反映されているか検証。

3. **実際のログおよび結果JSONの出力内容確認 (`v3/logs/`, `v3/results/`)**:
   - 最新の評価ログ (`v3_base_eval_parallel` 等) や出力 JSON において、全サンプル数が意図通り評価されているか（`limit` の有無、エラー吐き出しがないか）。
   - 計算されたスコアが適切な数値範囲に収まっているか、パース失敗による0点・異常値が発生していないか確認。

4. **結果の統合とドキュメント作成**:
   - `docs/verify_benchmark_evaluations/walkthrough.md` に各ベンチマークの検証結果、課題、修正状況を一覧化してまとめる。

---

## 変更ファイル

- `[NEW]` [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/verify_benchmark_evaluations/task.md)
- `[NEW]` [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/verify_benchmark_evaluations/implementation_plan.md)
- `[NEW]` [walkthrough.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/verify_benchmark_evaluations/walkthrough.md)

---

## 検証方法
- `grep` および `view_file` によるスクリプトコードとログファイルの静的検証。
- 16個のベンチマークすべてのログ・結果JSONから抽出した実測スコアとサンプル数の整合性確認。
