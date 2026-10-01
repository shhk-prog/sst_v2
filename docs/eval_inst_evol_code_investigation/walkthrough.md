# 調査結果レポート: inst_evol_code の評価検証 (Walkthrough)

## 1. 調査概要
`inst_evol_code` (nickrosh/Evol-Instruct-Code-80k-v1) について、評価パイプライン ([eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_instruction_datasets.py)), メトリクス算出方式 (Perplexity & Similarity Score), 集計スクリプト、および実際の評価結果 JSON データを詳細に検証しました。

結論として、**`inst_evol_code` は Perplexity (PPL↓) と Similarity Score (Sim Score↑) の複合指標により、正確かつモデル特性に整合して評価・集計されています。**

---

## 2. 正常に評価されている主な理由

### ① 二重指標 (Perplexity & Similarity Score) による多角評価
- `eval_instruction_datasets.py` では、モデルの Target 出力確率に対する交差エントロピー損失から Perplexity (PPL↓) を算出し、同時に生成テキストと Target との文字列一致度 (Similarity Score↑) を測定しています。
- 単一の編集距離のみならず言語モデルとしての確信度 (PPL) を同時に評価することで、コード指示に対するモデルの適合度を多角的に捉えられています。

### ② 集計スクリプトにおける完全な整合性
- 集計スクリプト ([pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)) では、`similarity_score` (高精度選好) と `-perplexity` (低損失選好) が正しく抽出・パレート計算に組み込まれています。
- [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) においても 「`Evol-Instruct-Code (PPL↓)`」 および 「`Evol-Instruct-Code (Sim Score↑)`」 として正しく可視化されています。

---

## 3. 各ベースモデルの実効スコア (debug_limit320 環境)

| モデル名 | Perplexity (PPL↓) | Similarity Score (Sim Score↑) | ドメイン特性 |
| :--- | :--- | :--- | :--- |
| **WizardCoder** | **1.4106** | **15.10%** | コード特化モデルとして最高の言語確信度と生成類似度を達成 |
| **SafetyFT (seed44)** | 1.9829 | 9.52% | 汎用 Llama-2-7b ベース |
| **WizardMath** | 1.8972 | 7.52% | 数学モデル |
| **MedAlpaca** | 2.1502 | 7.56% | 医療モデル |

コード特化モデルである **WizardCoder** (PPL: 1.41, Sim: 15.10%) が他ドメインモデルに対して圧倒的な優位性を示しており、ドメイン能力の差が極めて客観的かつ適正に評価されていることが確認されました。
