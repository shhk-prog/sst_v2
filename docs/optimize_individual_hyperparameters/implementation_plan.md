# ハイパーパラメータ個別最適化と評価ロジック改善の実装計画

本計画は、`model1_math`, `model2_coding`, `model3_medicine` の各ファインチューニングモデルのハイパーパラメータ（エポック数、学習率）を個別に調整・最適化し、さらに `model3` の精度を 80% (0.8) 以上に引き上げることを目的としています。また、TeleQnA ベンチマークにおける出力プレフィックス崩れによる正解判定失敗（model1 等）に対処するため、評価のパース処理を改善します。

## ユーザー確認事項

> [!IMPORTANT]
> - 今回は各モデルで個別の学習率やエポック数を適用するため、ログおよび結果フォルダ名の命名規則 `model名_ep_bs_lr` に完全に追従するよう、自動で `RUN_ID` を決定し実行する仕組みにスクリプトを修正します。
> - 各モデルの提案パラメータは以下の通りです。
>   - **model1_math**: `EPOCHS=2.0`, `LR=1.0e-5` (過学習と破滅的忘却の抑制)
>   - **model2_coding**: `EPOCHS=2.0`, `LR=1.0e-5` (アライメント崩れの抑制)
>   - **model3_medicine**: `EPOCHS=4.0`, `LR=2.0e-5` (医学知識のさらなる定着と 0.8 以上への引き上げ)

## 提案する変更内容

### 1. 評価ロジックの改善 (TeleQnA)

#### [MODIFY] [run_eval_telecom.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_eval_telecom.sh)
- 判定ロジック `is_correct = correct_option.lower() in pred.lower()` を、正規表現を用いた頑健なオプション番号パース処理に変更します。これにより、モデルが `"option 1"` と言わずに単に `"1"` と答えた場合や、文末に数字を出力した場合でも、正解のオプション番号と合致していれば正しく正解としてカウントできるようにします。

### 2. 学習スクリプトのリファクタリング (パラメータ引数化・環境変数化)

#### [MODIFY] [run_model1_math.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_model1_math.sh)
#### [MODIFY] [run_model2_coding.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_model2_coding.sh)
#### [MODIFY] [run_model3_medicine.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_model3_medicine.sh)
- 各スクリプトでハードコードされている `EPOCHS` や `LR` などのハイパーパラメータを、環境変数が指定されている場合はそちらを優先するように変更します。これにより、呼び出し元のマスターシェルスクリプトから柔軟にパラメータを流し込めるようにします。
- デフォルト値は提案値（`model1`: ep2.0/lr1e-5, `model2`: ep2.0/lr1e-5, `model3`: ep4.0/lr2e-5）に設定します。

### 3. マスター実行スクリプトの修正

#### [MODIFY] [run_full_pipeline.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_full_pipeline.sh)
- 個別に変更された `RUN_ID` を定義し、各モデルの学習時に対応する `EPOCHS` や `LR` を環境変数としてエクスポートしてから `run_model*.sh` を実行するようにします。
- 各モデルの評価時には、対応する `RUN_ID_X` を渡して `run_all_benchmarks.sh` を呼び出すように同期します。
- ログと結果フォルダは命名規則 `model名_ep_bs_lr` に完全に従うようになります。

---

## 検証計画

### 1. 自動テスト・スクリプトの実行
リファクタリングおよびパラメータ設定完了後、以下のコマンドを実行してフルパイプラインの再学習およびベンチマーク評価を行います。
```bash
cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT
./run_full_pipeline.sh > logs/full_pipeline_optimized_hyperparameters.log 2>&1
```

### 2. 手動確認
- 生成されたログファイル `logs/full_pipeline_optimized_hyperparameters.log` を確認し、学習・評価が正常終了したか確認します。
- `results/` ディレクトリ内に以下の規則に準拠した名前のフォルダが作成されているか確認します：
  - `model1_math_ep2.0_bs16_lr1.0e-5`
  - `model2_coding_ep2.0_bs16_lr1.0e-5`
  - `model3_medicine_ep4.0_bs16_lr2.0e-5`
- 評価スコアを抽出し、BaseModelおよび前回の結果（`ep3.0_bs16_lr2.0e-5`）と比較した性能の推移をレポート（`walkthrough.md`）にまとめます。特に、`model3` の主要評価（pubmedqa など）が 0.8 以上を達成できているかを確認します。
