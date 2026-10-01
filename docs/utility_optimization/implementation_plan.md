# Utility Fine-Tuning 性能向上のための実装計画

現状、学習率 1e-4 および 5e-4 での実験において、モデルの有用性スコア（特に HumanEval や GSM8K）がベースモデルと比較して大幅に低下（Catastrophic Forgetting）していることが確認されました。この問題を解決し、Utility 性能を最大限に引き出すための修正を行います。

## ユーザーレビューが必要な項目
> [!IMPORTANT]
> 以下の変更により、学習時間が短縮され、モデルの汎化性能が向上することが期待されますが、安全性（Safety）に関する制約が緩くなる可能性があります。今回の目的が「Safetyは無視してUtilityを上げる」ことであるため、この方針で進めます。

## 提案される変更点

### 1. 学習スクリプトの改善 (`run_lora_ft.py`)
現在、モデルは指示（Prompt）と回答（Response）の両方で損失計算を行っています。これを回答部分のみに制限し、ベースモデルの指示理解能力を維持します。

#### [MODIFY] [run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py)
- TRL v1.4.0 の仕様に合わせ、データセットを `text` フィールドではなく `messages` (Conversational形式) に変換する。
- `SFTConfig` で `assistant_only_loss=True` を設定し、自動的にアシスタントの回答部分のみが学習対象になるようにする（`DataCollatorForCompletionOnlyLM` は最新版で廃止されたためこの方法に切り替えます）。
- LoRA の `lora_alpha` を `rank * 2`（32）に設定し、学習の安定性を向上させる。

### 2. 実行パラメータの最適化 (`run_phase2.sh`)
学習率が高すぎることが忘却の主な原因と考えられます。

#### [MODIFY] [run_phase2.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_phase2.sh)
- 学習率を `5e-5` に下げ、より安定した収束を目指す。
- エポック数は最大 `5` とし、`EarlyStoppingCallback`（patience=3）により過学習を防止する。
- 実験名を `lr5e-5_ep5_opt` 等に変更し、新しい実験として管理する。

## 検証計画

### 自動テスト
- `run_lora_ft.py` の修正後、ダミーデータを用いて損失計算が回答部分のみで行われているかを確認する小規模なテストを実行。

### 手動検証
- 新しい設定で `utility_lora` (Finance) および `coding_lora` (Magicoder) を学習。
- 学習完了後、既存の評価パイプラインを実行し、HumanEval および GSM8K のスコアがベースモデルと同等以上に回復しているかを確認。
