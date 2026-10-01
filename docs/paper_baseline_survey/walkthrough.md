# 調査完了報告 (Walkthrough)

本調査では、提示されたモデルマージおよび安全性アライメント関連の10本の論文について、それぞれの再現実験で用いられている**比較Baseline手法**、**評価設定（ベースモデル、評価データセット、指標など）**、および**公式コードの有無**を詳細に調査し、レポートとしてまとめました。

## 完了した作業
- **論文詳細調査:** 提示された10本の論文URLおよびWeb検索を利用して、各論文の再現実験における比較Baseline手法と評価方法を調査しました。
- **レポートの作成:** 調査した情報を「公式コードがあるもの」と「ないもの」に分類し、各論文の要点をまとめた `baseline_report.md` を作成しました。
- **比較表の作成:** 全10本の論文を俯瞰できるマトリクス比較表を作成しました。
- **進捗管理:** `task.md` に従って進捗を適切に管理しました。

## 成果物へのリンク

- **調査レポート本体:** [baseline_report.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_baseline_survey/baseline_report.md)
  - 公式コードの有無で分類し、各手法の特徴、再現実験でのBaseline、評価モデル、評価データセット、指標をまとめています。
- **タスクリスト:** [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_baseline_survey/task.md)
- **実装計画:** [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_baseline_survey/implementation_plan.md)

## 調査結果の要約

### 1. 公式コードがある論文 (6本)
1. **Merging Models with Fisher-Weighted Averaging (NeurIPS 2022)**
   - 対角Fisher情報を重要度重みとしたパラメータマージ。
2. **Model Merging by Uncertainty-Based Gradient Matching (ICLR 2024)**
   - 勾配の不一致を二次近似で緩和する不確実性ベースの勾配マッチング。
3. **Fisher Mask Nodes for Language Model Merging (LREC-COLING 2024)**
   - Attention/FFNのmask nodeのFisher情報を利用した高速マージ。
4. **Dynamic Fisher-weighted Model Merging via Bayesian Optimization (NAACL 2025)**
   - スケーリング係数をベイズ最適化＋Fisher情報で動的に探索・マージ。
5. **LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint (ACL 2025)**
   - 重要パラメータのLocation, Election, Disjoint操作による安全性衝突の回避。
6. **SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging (2025-2026)**
   - 安全部分空間とのコサイン類似度に基づいて、乖離した層（レイヤー）のみを選択的に安全アライメントモデルとマージ。

### 2. 公式コードがない論文 (4本)
1. **Task-Aware Model Merging via Fisher-Weighted Median (ICLR 2026, withdrawn)**
   - 符号/冗長性干渉緩和＋対角Fisherを考慮した重み付き中央値集約（DRIFT-MEDIAN）。
2. **Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs (2026)**
   - キャリブレーション不要で対角Fisher情報から各層の最適マージ係数を決定。
3. **AlignMerge - Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints (2025)**
   - 局所Fisher空間内での幾何学的な制約を用いたアライメント部分空間からの逸脱防止マージ。
4. **Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs (2024)**
   - ドメイン更新ベクトルとアライメント更新ベクトルの線形補間（MergeAlign）。
