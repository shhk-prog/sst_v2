# 調査結果レポート: general_mmlu の評価検証 (Walkthrough)

## 1. 調査概要
`general_mmlu` (Hendrycks MMLU, 全57サブタスク) について、評価パイプライン、タスク設定、集計スクリプト、および実際の評価結果 JSON データを詳細に検証しました。

結論として、**`general_mmlu` は正しく適切に評価されており、スコア集計も正常に機能しています。**

---

## 2. 正常に評価されている主な理由

### ① 対数尤度 (Loglikelihood) 評価方式の採用
- MMLU は生成モデルに自由記述させる方式ではなく、4 つの選択肢 (A, B, C, D) に対する条件付き対数尤度を比較する `loglikelihood` 方式で評価されています。
- テキスト生成のフォーマット崩れやプロンプト指示の解釈違いによる失点が発生せず、モデルの知識量を客観的・定量的に測定できています。

### ② メトリクス抽出と集計処理の完全な整合性
- 評価結果 JSON の `results.mmlu` において、全 57 タスクの加重平均スコアが `acc,none` として正しく記録されています。
- 集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py) / [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py)) では、`preferred_keys` に `"acc,none"` が含まれているため、MMLU の全体精度を正確に読み出してテーブルやグラフに反映できています。

---

## 3. 各ベースモデルの実効スコア (debug_limit320 環境)

| モデル名 | MMLU 全体正解率 (Acc) | STEM | Humanities | Social Sciences | Other |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MedAlpaca** | **51.04%** | 40.87% | 52.88% | 59.92% | 52.12% |
| **WizardMath** | **42.23%** | 32.50% | 47.30% | 46.39% | 44.18% |
| **SafetyFT (seed44)** | **40.49%** | 32.96% | 44.49% | 44.14% | 42.06% |
| **WizardCoder** | **32.96%** | 30.18% | 34.62% | 35.66% | 31.81% |

4 択問題のランダム確率 (25%) に対し、各モデルの特性（MedAlpacaが高スコア、コード特化のWizardCoderは低め等）が反映された非常に妥当な値となっており、異常値やエラー判定は見られません。

---

## 4. 補足・評価時の考慮事項

- **few-shot 設定**:
  - 現在は `num_fewshot=0` (0-shot) で評価されています。
  - loglikelihood 方式のため 0-shot でも正常に機能していますが、公式論文（Hendrycks et al.）や Open LLM Leaderboard の標準値（5-shot）と比較したい場合は、必要に応じて `num_fewshot: 5` を設定することも可能です。
