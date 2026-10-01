# タスクリスト

## Phase 1: 評価フォーマットの修正 (完了)
- [x] 性能低下問題の調査・分析計画の策定
- [x] 評価ログの調査・Template Mismatch の特定
- [x] 評価パイプラインの修正 (`--apply_chat_template`)
- [x] 本番評価の実施と結果確認 (GSM8Kで改善確認)

## Phase 1.5: データクリーニングの実験 (完了)
- [x] 学習データのクリーニング（解説文の除去）
- [x] 再学習と評価（HumanEvalが悪化、GSM8Kが改善することを確認）

## Phase 2: コーディング性能 (HumanEval/MBPP) の向上へ向けた再設計
- [/] 改善計画の策定 (`implementation_plan.md` 更新)
- [ ] クリーニング版モデルの HumanEval 評価ログ (`samples_humaneval_*.jsonl`) を解析し、失敗原因を特定する
- [ ] `prepare_datasets.py` を修正し、Python コードのみを抽出するようにドメイン特化を行う（不要な言語の排除）
- [ ] `run_lora_ft.py` を修正し、Early Stopping 設定の見直し（または完走）を行う
- [ ] `run_lora_ft.py` で `assistant_only_loss` の無効化を検討する
- [ ] 再学習 (`coding_lora_python_only` など) を実行する
- [ ] 評価 (`--apply_chat_template`) を実行し、HumanEval / MBPP が改善したか確認する
- [ ] 結果を `walkthrough.md` にまとめる

