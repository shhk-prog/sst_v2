# 実装計画: Day 1（数学評価修復・SafeMERGE H3 監査・rope_theta 準備・MergeBench 確認）

## 1. 数学有用性評価の修復（GSM8K Alpaca-CoT）
- **原因**: `v3/scripts/eval/eval_utility.py` が `### Instruction:\nQuestion: ...\nAnswer:\n\n### Response:\n` を送信したため、`WizardMath-7B-V1.0` が CoT をスキップして `\nThe answer is: 12.` のように即答し 6.25% まで崩壊していた。
- **実装**: `v5/scripts/eval_math_alpaca_cot.py` と `v5/scripts/run_math_alpaca_reeval.sh` を作成。WizardMath 公式の Alpaca-CoT プロンプト（`Below is an instruction... ### Response: Let's think step by step.`）で `openai/gsm8k` (test 先頭 320 件) を vLLM 推論し、1 件ごとに原子保存・途中再開・GPU 情報記録を行う。まず `smoke` モードで `WizardMath-7B-V1.0` 単体が 50% 前後を出すことを確認した後、`seed 42/43/44` モードで `safety+math` 全モデルを再評価する。

## 2. SafeMERGE H3 監査（5.7 節【結果待ち】の解消）
- `v5/scripts/audit_safemerge_layers.py` で `v3/models/merged/*safemerge*` の全 9 件の `safemerge_layer_weights.json` および `seed42` 3 ドメインの実際の重み差分（対 base / 対 util / 対 safe、target & norm 層）を CPU で計測し、`v5/outputs/sok_audit/safemerge_h3_audit.{json,md}` に出力する。

## 3. P4 `rope_theta` 因果切り分け実験の準備
- `v5/scripts/prepare_rope_theta_ablation.py` で `safety+code` (`α=0.6, seed42`, TA / DARE / diagonal_sst) の重みへのゼロコピーシンボリックリンクと `rope_theta=1000000.0` にのみ書き換えた `config.json` を `v5/models/rope_theta_ablation/` に生成し、`v5/scripts/run_rope_theta_ablation.sh` で 1 件逐次保存評価を実行可能にする。

## 4. MergeBench モデル群の実在・アクセス確認
- HuggingFace API で `MergeBench` 全 40 モデルの一覧と gated 状態を確認し、`Llama-3.1-8B-Instruct` ベースモデルのキャッシュ有無を確認する。
