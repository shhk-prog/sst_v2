# 修正内容の確認 (Walkthrough)

5つの感情分析タスクすべてを `roberta-base` から個別にファインチューニングされた Expert として対称的にマージできるよう、パイプラインの修正を行いました。

## 変更内容

### 1. [fisher_roberta_base_run.json](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/scripts/fisher_roberta_base_run.json) (新規作成)
ベースモデルとなるオリジナルの `roberta-base` に対して Fisher 情報（Hessian）を推定するための設定ファイルを作成しました。推定用データセットには `imdb` を使用します。

### 2. [run_model_merging_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging/run_model_merging_pipeline.sh) (修正)
- 準備処理フェーズに `roberta-base` の Fisher 推定（`fishers/pretrained_roberta_base` への出力）を追加しました。
- マージ処理（`uncertainty_based_gradient_matching.py`）の引数を修正し、マージの基準点に `roberta-base` を指定し、マージ対象（`ft_model_name_or_paths`）に `imdb` を含む 5 つの Expert モデルすべてを指定する構成に修正しました。
- スケーリング因子 `scaling_factors_ft` に imdb に対応する `25000` を追加しました（`25000,112000,8530,67349,180000`）。

---

## 検証方法（依頼）

以前の非対称構成で出力された古いマージモデルや評価結果をクリアした上で、再実行を行ってください。

1. ワークスペースのディレクトリに移動します：
   ```bash
   cd /mnt/nas/home/hiromi/src/sst_v2/baseline/iclr2024-model-merging
   ```
2. 古いマージモデルおよび評価結果を削除します：
   ```bash
   rm -rf models/merged
   rm -f metrics/merged_*.json
   ```
3. パイプライン実行スクリプトを走らせます：
   ```bash
   ./run_model_merging_pipeline.sh
   ```
4. ベースモデルの Fisher 推定および、対称な構成でのモデルマージ、最終評価がエラーなく完了することを確認します。
5. 出力される精度サマリーテーブルが、非対称な構成の時と比較して向上していること（特に imdb での極端な劣化が解消していること）を確認します。
