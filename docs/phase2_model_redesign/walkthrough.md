# フェーズ2 再設計 実装完了レポート

ユーザーの要件と承認された計画に基づき、SST-Merge フェーズ2における Utility 特化FTモデルの性能向上および安全性の汎化性能を評価するためのスクリプト群の実装を完了しました。

## 実装内容サマリー

### 1. データセット構成の刷新
- **Utility (Finance)**: センチメント分類の FinGPT から、推論型QAの `gbharti/finance-alpaca` に変更しました。
- **データ分割**: Finance および Coding (Magicoder) データセットについて、In-Distribution 評価用に 90%/10% (train=4500, eval=500) の分割を実装しました。
- **Safety OOD**: LED-Merging等で標準的に使用されている汎用的な安全性評価ベンチマーク `HarmBench` を新規追加しました（HuggingFaceがダウンした場合のCSVフォールバックも実装済み）。
- 関連ファイル: `v2/scripts/data_prep/prepare_datasets.py`

### 2. ファインチューニングのハイパーパラメータ改善
- **過学習防止**: 
  - デフォルトの学習率を `2e-4` から `1e-4` へ低減しました（finance, codingで適用）。
  - ウォームアップ `warmup_ratio=0.05` を追加し、学習初期の不安定性を軽減しました。
  - バリデーション用データセット（`--eval_dataset_path`）を渡し、`EarlyStopping` および `load_best_model_at_end=True` を有効化して、ベストなチェックポイントを保存するように修正しました。
- 関連ファイル: `v2/scripts/fine_tuning/run_lora_ft.py`

### 3. ID / OOD 評価パイプラインの整備
- **Safety**: 
  - [ID] AdvBench + TrustLLM（FTデータ）の評価は現状維持。
  - **[NEW]** [OOD] `run_harmbench_eval.py` を新規作成。学習データに含まれない HarmBench プロンプトによる ASR（攻撃成功率）を測定し、安全性汎化を評価します。
- **Utility**:
  - [OOD] MMLU, HumanEval, MBPP, GSM8K（lm_eval）での汎化性能評価は維持。
  - **[NEW]** [ID] `run_utility_id_eval.py` を新規作成。FTデータの10%（eval_split）を利用し、ROUGE-L スコアを用いて生成結果の正確性を評価します。

### 4. レポート生成の拡張
- `summarize_results.py` のマークダウン表を全面更新し、ID/OODの区分けを明確にしました。
  - 表1: 安全性評価に AdvBench ASR (ID) と HarmBench ASR (OOD) を併記。
  - 表2: 有用性評価に 金融 ID (ROUGE-L) と コード ID (ROUGE-L) の列を追加。
  - 表3: 総合評価の計算式に HarmBench (OOD) ASR を採用し、より厳密な汎化性能に基づくスコア算出に変更。

### 5. オーケストレーション (`run_phase2.sh`)
- 上記のすべての変更を `run_phase2.sh` に統合し、Step 1〜11 の完全なエンドツーエンドパイプラインとして整理しました。

## 次のステップ

すべてのスクリプトの構文チェックは完了しています。

1. **スモークテストの実施**（任意）
   問題なく動作するかどうか、小さいデータセットでテストを行う場合は以下のコマンドを実行してください。
   ```bash
   cd /mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning
   LIMIT_UTILITY=10 N_SAFETY_ID=10 N_SAFETY_OOD=10 N_UTILITY_ID=10 bash run_phase2.sh
   ```

2. **本番の学習と評価**
   準備が整い次第、ターミナルで本実行を開始してください。
   ```bash
   cd /mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning
   RUN_NAME="lr1e-4_ep3_v2" bash run_phase2.sh
   ```

問題点や修正のご要望があればお知らせください。
