# 実装計画: 指示書 v2 準拠の 4 点修正・LED-Merging 重み監査・WizardCoder 公式 HumanEval 検証準備

## 1. 背景と目的
ユーザーからの 4 点の修正指示および `v5/docs/実装指示書 v2（11月26日）.md` に基づき、以下を実施する。
1. `rope_theta` 切り分け比較表の結論を §4.4 の主張範囲に修正し、部分的効果を残したうえでコード有用性列に「暫定」を付記する。
2. 新 GSM8K × 安全性の比較を HarmBench / WildGuard / StrongREJECT の **3 判定器それぞれ**で安全性を揃えて出力し、結合 VRR（「どちらか崩壊で無効」）の下限を `90%` に統一する。
3. 指示書 v2 第 1 節（`v5/results/runs/YYYYMMDD-HHMM_<name>/` + `RUN.md` + `env.json` + `commands.sh` + `INDEX.md`）を `sst_v2/v5` に導入し、既存 2 実験＋新規解析 3 件を正規台帳へ登録する。
4. 指示書 v2 §2.5 の最優先 2 件（#2 LED-Merging 重み監査を CPU で即完了、#1 WizardCoder 単体 HumanEval 崩壊の原因特定と公式検証ゲート実行スクリプト整備）を実施する。

## 2. 作成・修正ファイル
- `v5/scripts/new_run.py`: §1.1–1.4 準拠のランフォルダ生成・上書き防止（`-2` 付与）・`env.json` 記録・`INDEX.md` 追記ツール。
- `v5/scripts/summarize_rope_theta_ablation.py`: `--run-dir` 対応、結合 VRR / 従来 VRR / 拡張単独 VRR 併記、Code 列「暫定」表記、§4.4 準拠の結論文章。
- `v5/scripts/analyze_math_alpaca_cot.py`: `--run-dir` 対応、`--vrr-min 90.0` 既定化、3 判定器別の線形補間表（「到達せず」対応）＋ 3 判定器別ペアードブートストラップ 95% CI、参照点 3 種描画。
- `v5/scripts/audit_led_merging_weights.py`: §4.2 準拠の単精度 (`fp32`) ストリーミング重み退化監査スクリプト。
- `v5/configs/expert_eval_spec.yaml`: §2.1 準拠の実環境トラック専門モデル評価仕様書（WizardMath / WizardCoder / MedAlpaca）。
- `v5/scripts/eval_code_wizardcoder_official.py` / `v5/scripts/run_wizardcoder_verify.sh`: §2.2 / §2.5 #1 準拠の WizardCoder 公式 Alpaca-Code HumanEval 評価・自動検証ゲート・20 件目視表 (`samples_review.md`) 生成スクリプト。
- `v5/tests/test_v2_spec_tools.py`: 上記ツール群の単体テスト。

## 3. 制約
- `v3/`・`v1/`・`v2/` および既存結果フォルダは一切変更・移動・削除しない（NFR2・指示書 v2 §6）。
- CPU コマンドはすべて `CUDA_VISIBLE_DEVICES=""` で実行する。
