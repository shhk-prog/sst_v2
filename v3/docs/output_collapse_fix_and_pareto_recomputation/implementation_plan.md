# 実装計画: 出力崩壊修正および正常応答のみによる Pareto Frontier 再計算

## 概要と目的
SST (Selective Sparse Tuning) の評価結果において、`safety+math` (2ドメイン単一マージ) では意図通りの Pareto トレードオフ制御が確認されていますが、`safety+code`, `safety+medical`, および `safety+math+code+medical` (4ドメイン多重マージ) では広範な出力崩壊 (Model Collapse / Gibberish) が生じる問題が発生しています。

出力崩壊が発生したサンプルは、HarmBench 等の安全判定器によって「有害コンテンツ未検出 (Harmful=No → ASR=0%)」と判定されるため、**「モデルが破壊されたことによる見かけ上の安全性の跳ね上がり」** という重大な評価の歪みを生み出しています。

本計画では、以下の2つの主要な課題に取り組みます：
1. **アルゴリズム修正 (Algorithmic Remediation)**: コード・医療・多重マージにおけるパラメータノルム増幅と Fisher 情報量のスケール不均衡を補正し、出力崩壊を抑制・防止する。
2. **評価パイプラインの正常化 (Fair Pareto Evaluation)**: Gibberish/Repetition 判定ロジックにより崩壊応答を除外し、「正常応答 (Valid Responses)」のみに基づいた厳密な Pareto Frontier および AUC の再計算を行う。

---

## 修正・実装のアプローチ

### 1. 出力崩壊原因の解明と対策 (Algorithmic Fixes)

- **原因①: ドメイン間の Delta Weight ノルム不均衡 (Norm Explosion)**
  - Code/Medical モデルの LoRA / FT 重み変化量 $\Delta W$ の L2 ノルムが Safety や Math に比べて過大である可能性。
  - **対策**: 各タスクベクトルのノルムを正規化 ($\Delta W_{normed} = \frac{\Delta W}{\|\Delta W\|} \times \bar{S}$) してから合成する **Task Vector Norm Standardization** を導入。

- **原因②: Multi-Domain 合成における Fisher スケールの偏り**
  - SST の Fisher 情報行列 (FIM) 計算において、Code/Medical データセットに対する損失勾配のスケールが Safety データの勾配と大きく異なり、対角比率 $F_{harmful} / F_{benign}$ の閾値マスクが偏る。
  - **対策**: ドメイン毎の FIM の平均値を 1.0 にスケーリング（FIM Standardized SST）し、公平な重要度マスクを構築する。

- **原因③: 特定アライメント層の破綻**
  - 4ドメインの線形結合において、特定の層 (MLP down_proj / gate_proj) でロジット値が極端な値を取り、Repetition Loop を引き起こす。
  - **対策**: スケーリング係数 $\alpha$ の適用時に Layer-wise Norm Clip または 係数の適応的調整を実施。

### 2. 正常応答フィルタリングと Pareto Frontier 再計算 (Fair Pareto Evaluation)

- **フィルタリング条件 (Valid Response Criterion)**:
  - **Gibberish Filter**: `JailbreakBench Gibberish Ratio` または PPL / N-gram 重複率が閾値以上の応答を `Invalid` と認定。
  - **Min Length / Non-empty**: 正常な回答テキストを生成しているか確認。
- **指標再計算**:
  - **Harmful ASR (Valid Only)**: `Invalid` 応答を ASR=0% にカウントせず、計算対象から除外（または Valid 応答中での Harmful 比率を算出）。
  - **Valid Utility Score**: 崩壊した推論結果を除外し、モデルが「意味のある応答を出した中での正解率」および「Valid Response Ratio (全応答中の正常出力割合)」を個別に報告。
- **Pareto Frontier Plot**:
  - X軸: 正常応答のみで算出した Utility (Math/Code/Medical Ave %)
  - Y軸: 正常応答のみで算出した Safety (100 - Harmful ASR %)
  - 正常応答率 (Valid Ratio %) をポイントのサイズや透明度で表示し、壊れたモデルを判別可能にする。

---

## 変更ファイル一覧

#### [MODIFY] [merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge.py)
- Norm Standardization / FIM Standardized SST のオプション追加。

#### [MODIFY] [mergers.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers.py)
- 多重マージにおける重みノルム制御および FIM スケーリング処理の更新。

#### [MODIFY] [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/pareto_auc.py)
- Gibberish 応答をフィルタリングし、正常応答のみで Pareto Frontier および AUC を再計算・描画するロジックを実装。

#### [MODIFY] [generate_paper_summary_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_paper_summary_tables.py)
- Valid Response Ratio を集計表に追加し、正常応答のみでの平均スコアを出力するオプションを拡充。

---

## 検証計画

### 1. 自動テスト・数値検証
- `python3 v3/scripts/analysis/pareto_auc.py --merge_target safety+code --filter_gibberish` を実行し、正常応答のみでの Pareto Frontier が正しく算出されるか検証。
- `python3 v3/scripts/analysis/pareto_auc.py --merge_target safety+math+code+medical --filter_gibberish` で 4ドメインの Pareto Frontier を再描画。

### 2. 定性検証・モデル応答確認
- 修正後の SST (Norm Standardized SST) で `safety+code`, `safety+medical`, 4ドメインマージのモデルを出力・評価し、Gibberish N（崩壊数）が大幅に削減されることを確認。
