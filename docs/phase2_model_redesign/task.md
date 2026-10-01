# フェーズ2 実装タスクリスト

## 1. データ準備 (prepare_datasets.py)
- [x] 現状確認完了
- [ ] `prepare_utility_finance_data()`: FinGPT-sentiment → finance-alpaca に変更
  - HuggingFace: `gbharti/finance-alpaca` を使用
  - train/eval 分割: 90%/10% (train=4500, eval=500)
  - 保存先: `utility_finance.json` (train) と `utility_finance_eval.json` (eval)
- [ ] `prepare_harmbench_data()`: HarmBench データセット追加
  - `walledai/HarmBench` または公開CSV版を使用
  - 保存先: `safety_harmbench.json`
- [ ] `prepare_magicoder_eval_data()`: Magicoder eval split 追加
  - 5000件のうち末尾500件をeval用に確保
  - 保存先: `utility_coding_eval.json`
- [ ] main() に新関数を追加

## 2. FT スクリプト改善 (run_lora_ft.py)
- [ ] `--warmup_ratio` 引数追加 (デフォルト 0.05)
- [ ] `--eval_dataset_path` 引数追加 (バリデーション用)
- [ ] `save_strategy="best"` + `load_best_model_at_end=True` に変更
- [ ] `eval_steps` の設定追加

## 3. 安全性評価スクリプト拡張 (run_safety_eval.py)
- [ ] `--eval_type` 引数追加 (`id` = AdvBench+TrustLLM, `ood` = HarmBench)
- [ ] `--data_path` を複数対応または eval_type で自動切り替え
- [ ] task キーを `safety_id` / `safety_ood` に変更

## 4. HarmBench 評価スクリプト (run_harmbench_eval.py)
- [ ] 新規作成
- [ ] run_safety_eval.py の構造を流用
- [ ] HarmBench フォーマット対応
- [ ] task キー: `safety_harmbench`

## 5. Utility In-Distribution 評価 (run_utility_id_eval.py)
- [ ] 新規作成
- [ ] Finance ID eval: eval split で ROUGE/exact-match を計算
- [ ] Coding ID eval: eval split でコード生成の正確性を計算
- [ ] task キー: `utility_finance_id` / `utility_coding_id`

## 6. run_phase2.sh の更新
- [ ] FT コマンドの更新:
  - utility FT: `utility_fpb.json` → `utility_finance.json`
  - learning_rate: 2e-4 → 1e-4 (finance), 1e-4 (coding)
  - warmup_ratio: 0.05 追加
  - eval_dataset_path 追加
  - epochs: 5 → 3
- [ ] 評価ステップの追加:
  - Step 4 (既存): AdvBench+TrustLLM ASR (safety ID)
  - Step 5 (新規): HarmBench ASR (safety OOD)
  - Step 6 (既存更新): Finance MMLU (utility OOD)
  - Step 7 (新規): Finance ID eval
  - Step 8 (既存更新): Coding HumanEval/MBPP/GSM8K (utility OOD)
  - Step 9 (新規): Coding ID eval
  - Step 10 (既存): General (ARC/HellaSwag)
  - Step 11 (既存): XSTest over-refusal

## 7. 最終確認
- [ ] スクリプト動作テスト (スモークテスト: --limit 50)
- [ ] summarize_results.py の更新 (新しいtaskキーに対応)
