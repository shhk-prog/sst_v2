# 調査結果レポート: medical_pubmedqa の評価検証 (Walkthrough)

## 1. 調査概要
`medical_pubmedqa` (bigbio/pubmed_qa) について、評価パイプライン、判定方式、集計スクリプト、および実際の評価結果 JSON データを詳細に検証しました。

結論として、**`medical_pubmedqa` は 3 択対数尤度比較方式 (`multiple_choice`) により、非常に正確かつ安定して評価・集計されています。**

---

## 2. 正常に評価されている主な理由

### ① 対数尤度比較 (`multiple_choice` / Loglikelihood) 評価の採用
- PubmedQA は自由文章の生成ではなく、医学論文のアブストラクトと質問文に対し 3 つの選択肢 (`yes`, `no`, `maybe`) の条件付き対数確率（確信度）を比較する方式で判定されます。
- フォーマット崩れやテキスト生成失敗の影響を全く受けず、モデルの文章理解・判断能力が安定して評価されています。

### ② 集計スクリプトにおけるキー指定の完全な整合性
- 集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)) の `preferred_keys` に `"acc,none"` および `"acc"` が正しく指定されており、正解率が正確に抽出されています。
- [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) においても 「`PubmedQA (Acc↑ %)`」 として正しく可視化されています。

---

## 3. 各ベースモデルの実効スコア (debug_limit320 環境)

| モデル名 | PubmedQA 正解率 (`acc,none`) |
| :--- | :--- |
| **WizardMath** | **89.38%** |
| **SafetyFT (seed44)** | **86.25%** |
| **WizardCoder** | **85.63%** |
| **MedAlpaca** | **80.63%** |

すべてのモデルで 80%〜89% の高い精度が得られており、評価ロジック・スコア抽出ともに異常は見られません。
