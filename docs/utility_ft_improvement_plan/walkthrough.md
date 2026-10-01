# Utility Fine-Tuning 改善 実装完了の確認 (Walkthrough)

承認いただいた実装計画に基づき、Utility FT における「過学習によるOOD性能低下」「評価フォーマットの非対称性」「repetition collapse」を解決するためのスクリプト群の改修を完了しました。

## 変更内容の概要

### 1. 評価フォーマットの非対称性の解消
- **対象ファイル:** `v2/scripts/fine_tuning/run_phase2.sh`
- **変更内容:** ベースモデルの OOD 評価ループにおいて、通常の `base_model` に加えて `--apply_chat_template` を適用した `base_with_template` を追加しました。これにより、学習時（Templateあり）と評価時でフォーマットが揃った公平なベースラインとの比較が可能になります。

### 2. Early Stopping と RUN_NAME の明示的運用
- **対象ファイル:** `v2/scripts/fine_tuning/run_phase2_python.sh`, `v2/scripts/fine_tuning/run_lora_ft.py`
- **変更内容:** 
  - `USE_ES=true/false` の環境変数によって、RUN_NAME が自動で `*_es` または `*_full` に切り替わるようにし、出力ディレクトリの上書きを防ぐ仕組みを導入しました。
  - `run_lora_ft.py` において、Early Stopping が発動して Best Checkpoint がロードされた場合、上書き保存と同時に `_best` というサフィックスを付けたディレクトリにも明示的にコピーを作成し、どのモデルが最適だったか運用上わかりやすくしました。

### 3. データパイプラインと Aggressive Clean 比較
- **対象ファイル:** `v2/scripts/data_prep/prepare_datasets.py`, `v2/scripts/fine_tuning/run_phase2_python.sh`
- **変更内容:** 
  - `prepare_datasets.py` にて `--clean-coding-output` を指定した際、出力ファイルを `utility_coding_python_clean.json` として別名保存するように修正しました。
  - `run_phase2_python.sh` に `USE_CLEAN=true` を指定することで、このクリーンデータを利用した学習に簡単に切り替えられるようにしました。

### 4. 推論・評価時の Generation Config 調整
- **対象ファイル:** `v2/scripts/fine_tuning/run_utility_eval.py`
- **変更内容:** `lm_eval` 実行時に `repetition_penalty` や `temperature` などの推論パラメータを渡せるよう、`--gen_kwargs` オプションを追加しました。
  - **使い方例:** `python run_utility_eval.py ... --gen_kwargs "repetition_penalty=1.05,temperature=0.7"`

### 5. ハイパーパラメータ調整と学習カーブ分析
- **対象ファイル:** `v2/scripts/fine_tuning/run_phase2_python.sh`, `v2/scripts/fine_tuning/analyze_learning_curves.py` (新規追加)
- **変更内容:** 
  - `run_phase2_python.sh` で `LR`, `EPOCHS`, `PATIENCE` を環境変数として受け取れるようにし、連続したグリッドサーチをシェルスクリプトから簡単に実行可能にしました。
  - 学習完了後に `trainer_state.json` を読み込み、`train_loss` と `eval_loss` の推移をターミナルやCSVに出力する専用スクリプト `analyze_learning_curves.py` を作成しました。過学習の開始ポイント (epoch 0.6等) を素早く分析できます。

## 次のアクション・検証手順
以下のコマンドを用いて、改善された環境で実際に学習と評価を回すことができます。

1. **クリーンなデータでの Early Stopping あり学習 (推奨):**
   ```bash
   cd v2/scripts/fine_tuning
   USE_CLEAN=true USE_ES=true ./run_phase2_python.sh
   ```

2. **学習カーブの分析:**
   学習が完了したら、新設したスクリプトで Loss の推移を確認します。
   ```bash
   python analyze_learning_curves.py ../../models/Llama-3-8B/lr5e-4_ep10_python_es_clean/coding_lora
   ```

3. **推論ペナルティをかけた評価 (必要な場合のみ):**
   まだ repetition_collapse が発生する場合は、以下のように評価スクリプトを手動実行してペナルティをテストできます。
   ```bash
   python run_utility_eval.py --base_model meta-llama/Meta-Llama-3-8B \
       --adapter_path ../../models/Llama-3-8B/lr5e-4_ep10_python_es_clean/coding_lora_best \
       --model_name coding_lora_python_clean_rp \
       --eval_type coding --apply_chat_template \
       --gen_kwargs "repetition_penalty=1.05"
   ```
