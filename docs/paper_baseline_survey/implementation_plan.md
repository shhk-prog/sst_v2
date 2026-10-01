# 論文のBaselineおよび評価手法に関する調査計画

本計画は、ユーザーから提示された10本のモデルマージおよびアライメント関連論文について、それぞれの再現実験で用いられているbaseline手法、評価方法（データセット、モデル、指標など）、および公式コードの有無を調査・整理するためのものです。

## ユーザーレビューが必要な項目

> [!NOTE]
> 本調査はコードの変更を伴わない調査タスクです。調査レポートは `docs/paper_baseline_survey/baseline_report.md` に作成されます。
> 以下の調査項目とレポートのアウトラインについてご確認ください。

## 調査対象論文リスト

1. **Fisher Mask Nodes for Language Model Merging** (LREC-COLING 2024)
   - URL: https://aclanthology.org/2024.lrec-main.647.pdf
2. **Task-Aware Model Merging via Fisher-Weighted Median** (ICLR 2026 submission, withdrawn)
   - URL: https://openreview.net/pdf?id=uV8LGh2DCx
3. **Dynamic Fisher-weighted Model Merging via Bayesian Optimization** (NAACL 2025)
   - URL: https://aclanthology.org/2025.naacl-long.254.pdf
4. **Merging Models with Fisher-Weighted Averaging** (NeurIPS 2022)
   - URL: https://proceedings.neurips.cc/paper_files/paper/2022/file/70c26937fbf3d4600b69a129031b66ec-Paper-Conference.pdf
5. **Model Merging by Uncertainty-Based Gradient Matching** (ICLR 2024)
   - URL: https://arxiv.org/pdf/2310.12808
6. **Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs** (2026)
   - URL: https://arxiv.org/pdf/2603.21705
7. **AlignMerge - Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints** (2025)
   - URL: https://arxiv.org/pdf/2512.16245
8. **Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs** (2024)
   - URL: https://arxiv.org/pdf/2411.06824
9. **LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint** (ACL 2025)
   - URL: https://aclanthology.org/2025.acl-long.1055.pdf
10. **SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging** (2025-2026)
    - URL: https://arxiv.org/pdf/2503.17239

## 提案する変更（作成するファイル）

### 新規ドキュメントの作成

#### [NEW] [baseline_report.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_baseline_survey/baseline_report.md)
調査結果をまとめるレポートです。以下の構成で記述します：
- **公式コードがある論文のセクション**（各論文のメタデータ、コードリンク、baseline手法、評価設定、概要）
- **公式コードがない論文のセクション**（同上）
- **全体俯瞰・比較表**（手法名、ベースモデル、評価ドメイン、公式コードURLなどを俯瞰できるマトリクス）

## 検証計画

### 手動確認
- レポートにまとめられた各論文の情報（特に公式コードのURL、baseline手法、評価データセット）が、対応する論文PDFやWeb上の情報と一致していることを、論文を再確認して検証します。
- 生成されたマークダウンファイル（`baseline_report.md`）のリンクやフォーマットが正しいことを確認します。
