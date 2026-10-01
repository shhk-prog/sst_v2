# 調査結果レポート: math_gsm8k の評価検証 (Walkthrough)

## 1. 調査概要
`math_gsm8k` (openai/gsm8k) について、評価パイプライン、フィルタ設定、集計スクリプト、および実際の評価結果 JSON データを詳細に検証しました。

結論として、**`math_gsm8k` は柔軟な数値抽出フィルタ (`flexible-extract`) により、非常に正確かつ適正に評価・集計されています。**

---

## 2. 正常に評価されている主な理由

### ① 柔軟な数値抽出フィルタ (`flexible-extract`) の採用
- GSM8K の評価には `strict-match` と `flexible-extract` の 2 種類のフィルタが定義されています。
  - `strict-match`: `#### <number>` のような特定プレフィックス表記を必須とするため、多くのモデルで `0.0` になります。
  - `flexible-extract`: `(-?[$0-9.,]{2,})|(-?[0-9]+)` パターンにより、モデルが文章で解答を出力した場合（例: `"The answer is: 18."`）でも末尾の数値を正確に抽出します。
- 本リポジトリでは `flexible-extract` が正常に機能し、正しい解法に対する数値抽出が行われています。

### ② 集計スクリプトにおけるキー指定の完全な整合性
- 集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)) の `preferred_keys` では、`"exact_match,flexible-extract"` が上位に指定されています。
- これにより、`generate_tables.py` などでも 「`GSM8K (Flex EM↑ %)`」 として正確な正解率が集計・可視化されています。

---

## 3. 各ベースモデルの実効スコア (debug_limit320 環境)

| モデル名 | Flexible Exact Match (Flex EM) | Strict Match |
| :--- | :--- | :--- |
| **WizardMath** | **39.38%** | 0.00% |
| **WizardCoder** | **6.25%** | 0.00% |
| **SafetyFT (seed44)** | **4.06%** | 0.00% |
| **MedAlpaca** | **3.44%** | 0.00% |

数学特化モデルである `WizardMath` (39.38%) が他ドメインモデル（3%〜6%）を大きく引き離す高スコアを提示しており、モデルの数学解法能力の差が客観的かつきわめて明確に測定されています。
