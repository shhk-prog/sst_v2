# 再現確認ウォークスルー: model_merging (NeurIPS 2022)

再現実験の第1弾として実行した `model_merging` の結果の確認と、それに伴うドキュメント整備を完了しました。

## 実施した内容
1. **実行ログの確認**:
   - `baseline/model_merging/experiment_output.log` の全出力を解析し、途中でクラッシュすることなく `All experiments completed successfully.` まで正常終了していることを確認しました。
2. **評価結果のパースと整理**:
   - Target=rte に対する 5 つの Donor タスク（mnli, mrpc, sst-2, sts-b, qnli）における Isometric Merge と Fisher Merge の各スイープ結果から、Base Accuracy と Best Accuracy、最適なマージ係数を抽出しました。
3. **再現実験レポートの作成**:
   - 解析結果をまとめた詳細なレポート [reproduction_report.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_baseline_reproduction/reproduction_report.md) を作成しました。
   - レポートには、`mnli` とのマージによる精度向上（+1.45%）や、`sts-b` の Fisher Merge において発生した特異な精度低下現象についての考察などを記載しています。
4. **タスク進捗の更新**:
   - [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_baseline_reproduction/task.md) を更新し、`model_merging` のタスクを完了（`[x]`）とし、次の `iclr2024-model-merging` を進行中（`[/]`）にマークしました。

## 検証結果
- `model_merging` の実験はCPU環境（`venv_mm`）で約5時間をかけて無事に完走しており、出力された結果も理論値（マージなし時の精度が一定であることなど）と一致する正常な挙動を示しています。

## 次のステップ
- **手法 2/6: `iclr2024-model-merging` の再現実験の開始**
  - 次なるターゲットとして、`baseline/iclr2024-model-merging` の再現実験の準備と実行を行います。
