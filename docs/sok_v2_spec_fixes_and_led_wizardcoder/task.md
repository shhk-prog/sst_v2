# タスクリスト: 指示書 v2 準拠の 4 点修正・LED-Merging 重み監査・WizardCoder 検証ゲート準備

## 完了済みタスク
- [x] **修正 1 (`rope_theta` 結論の厳密化＋部分的効果の明記)**: `summarize_rope_theta_ablation.py` を修正し、「設定の取り違えだけでは崩壊を説明できない（語彙数 32,001 と系統の切り分けは未実施・1 点確認）」の範囲に統一しつつ、SST 結合 VRR `7.63% → 15.89%`・TA HB Cond.ASR `34.43% → 23.63%` の部分的効果を明記
- [x] **修正 2 (Code 有用性への「暫定」付記)**: `rope_theta_ablation_summary.md` の HumanEval / MBPP / Code Avg 全列に「暫定」を明記し、WizardCoder 単体検証（§2.5 #1）完了まで論文結論に使用しない旨を注記
- [x] **修正 3 (3 判定器ごとの同等安全性比較＋結合 VRR ≥ 90%)**: `analyze_math_alpaca_cot.py` を改修し、結合 VRR（従来規則・拡張規則のどちらか崩壊で無効）≥ 90%・従来/拡張単独 VRR 併記・3 判定器別の線形補間表（「到達せず」明示）・3 判定器別のペアードブートストラップ 95% CI・参照点 3 種描画を実装し、中間版（`120/138`）を実行・図確認
- [x] **修正 4 (指示書 v2 第 1 節のフォルダ管理導入)**: `v5/scripts/new_run.py` を作成し、`v5/results/runs/INDEX.md`・既存 2 実験の事後 `RUN.md`・新規 3 解析のランフォルダ一式（`RUN.md`, `env.json`, `commands.sh`, `logs/`, `outputs/`, `summary.json`）を整備
- [x] **最優先 #2: LED-Merging 重み・マスク監査 (`20261126-1344_led-merging-weight-audit`)**: 単精度重み統計（§4.2）で全 6 本が `0/291` テンソル更新（`Llama-2-7b-hf` 100.00% 一致）と確認し、`wandg` 出力先不整合（`random_score/` vs `wanda_score/`）＋語彙数不一致（32,000 vs 32,001）の二重サイレントスキップを特定
- [x] **最優先 #1: WizardCoder 単体 HumanEval 崩壊の原因特定＋公式検証ゲート準備**: `v3` で HumanEval が `5.49%` だった原因（`### Instruction:` ラップ後の応答に対する `lm-eval` の `prompt+resp` 重複連結・切断）を特定し、`v5/configs/expert_eval_spec.yaml`・`v5/scripts/eval_code_wizardcoder_official.py`・`v5/scripts/run_wizardcoder_verify.sh` を作成
- [x] 単体テスト追加（`v5/tests/test_v2_spec_tools.py`）→ `pytest v5/tests -q` 全 66 件 PASS・NFR2 確認

## 残タスク（GPU 実行・17 時以降）
- [ ] `iag-03` 空き GPU（GPU 2 等）で `run_wizardcoder_verify.sh` を実行し、WizardCoder 単体の HumanEval 検証ゲート（§2.5 #1）と 20 件目視確認（`samples_review.md`）を通す
- [ ] `seed 44` 完了後（17:00 ごろ）に新フォルダで `analyze_math_alpaca_cot.py` 最終集計を実行し、`20261126-1344_math-alpaca-analysis-interim` を「置き換え済み」に更新する
- [ ] ブートストラップ比較の主要点（SST α=0.8/1.0、TA α=0.6/0.8、DARE α=0.6）を GSM8K 全 1,319 問で再評価する
