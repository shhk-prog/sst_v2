# Utility FT 改善および集計スクリプト修正計画

実験結果から、Utility FT（金融/コーディング）において性能が低下し、かつ安全性が著しく悪化していることが確認されました。また、集計レポートの表示内容にも不備（MBPPスコアが0になる、MMLUの応答が数値になる等）が見つかりました。これらを解消するための修正を行います。

## ユーザーレビューが必要な項目

> [!IMPORTANT]
> **Utility FT への Safety データ混入 (Safety Replay)**
> `utility_lora` および `coding_lora` の学習時に、モデルの安全性を維持するため、少量の Safety データを混ぜる設定を導入します。これにより、有用性を高めつつ、有害プロンプトへの耐性を維持します。

## 提案される変更

### 1. 学習設定の適正化 (Step 3 関連)

#### [MODIFY] [run_phase2.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_phase2.sh)
- **学習率の引き下げ**: `5e-4` から `1e-4` に変更します。Llama-3 8B の LoRA では `5e-4` は高すぎて壊れるリスクが高いためです。
- **Safety Replay の導入**: `utility_lora` と `coding_lora` の学習時に `--safety_dataset_path` を指定し、`--safety_mix_ratio 0.1` (10% Safety) を設定します。

### 2. 学習スクリプトの修正

#### [MODIFY] [run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py)
- **プロンプトテンプレートの修正**: Llama-3 の公式テンプレート (`<|begin_of_text|>`, `<|start_header_id|>system<|end_header_id|>` 等) に準拠するように修正します。

### 3. 集計・レポートスクリプトの修正

#### [MODIFY] [summarize_results.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/summarize_results.py)
- **MBPP 判定の修正**: `lm-eval` の出力において MBPP のメトリクス名が `pass_at_1` になる場合があるため、これに対応します。
- **MMLU 応答表示の改善**: 多肢選択問題 (MMLU) において、対数尤度ではなく、選択した選択肢 (A, B, C, D) を表示するように修正します。
- **レポート表の不整合修正**: JSON 内のスコアと詳細セクションのスコア算出ロジックを統一します。

## 評価・検証計画

### 自動テスト
- 修正後の `run_phase2.sh` を短時間（例：1エポック、サンプル数制限）で実行し、エラーなく完了することを確認します。
- `summarize_results.py` を実行し、生成された `summary_report.md` の表示が正しい（MBPPが0でない、MMLUの応答が選択肢になっている）ことを確認します。

### 手動確認
- `utility_lora` の ASR が base_model 程度に維持されているか、かつ有用性指標（HumanEval等）が向上または維持されているかを確認します。
