# 調査結果レポート: medical_medqa_4options の評価検証 (Walkthrough)

## 1. 調査概要
`medical_medqa_4options` (GBaker/MedQA-USMLE-4-options-hf) について、評価パイプライン、判定方式、集計スクリプト、および実際の評価結果 JSON データを詳細に検証しました。

結論として、**`medical_medqa_4options` は対数尤度比較方式 (`multiple_choice`) により、極めて正確かつ適正に評価・集計されています。**

---

## 2. 正常に評価されている主な理由

### ① 対数尤度比較 (`multiple_choice` / Loglikelihood) 評価の採用
- MedQA は自由文章を生成させる方式ではなく、4 つの選択肢 (A, B, C, D) に対する条件付き対数尤度（確信度）を比較する方式で判定されます。
- 生成文の表記揺れや正規表現フィルタの不一致による誤判定が生じず、モデルの純粋な医療知識が安定的に評価されています。

### ② 集計スクリプトにおけるキー指定の完全な整合性
- 集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)) の `preferred_keys` に `"acc_norm,none"` および `"acc,none"` が指定されており、正解率が正確に抽出されています。
- [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) においても 「`MedQA (Acc Norm↑ %)`」 として正しく可視化されています。

---

## 3. 各ベースモデルの実効スコア (debug_limit320 環境)

| モデル名 | MedQA 正解率 (`acc_norm,none`) | 特徴・ドメイン整合性 |
| :--- | :--- | :--- |
| **MedAlpaca** | **43.44%** | 医療特化モデルとして最高の専門知識を発揮 |
| **SafetyFT (seed44)** | **31.88%** | 汎用 Llama-2-7b ベースモデルの標準値 |
| **WizardMath** | **31.88%** | 数学モデル（医療知識は標準） |
| **WizardCoder** | **22.50%** | コードモデル（4択ランダムの25%前後に近い） |

医療専門モデルである `MedAlpaca` (43.44%) が他モデルを大きく引き離して最高スコアを獲得しており、モデルの医療知識能力の差が極めて客観的かつ適切に測定されています。
