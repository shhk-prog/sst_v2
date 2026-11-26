# 修正内容の確認 (Walkthrough): 指示書 v2 準拠 4 点修正・LED-Merging 完全退化の特定・WizardCoder 検証ゲート準備

## 1. 実施した修正・新規実行（すべて `v5/results/runs/` に記録）
1. **ラン管理基盤 (`v5/scripts/new_run.py`, `v5/results/runs/INDEX.md`)**:
   - 既存 2 実験の事後 `RUN.md` を作成: `20261125-2347_math-alpaca-reeval`（実行中）、`20261126-1239_rope-theta-ablation-eval`（完了）。
   - 新規解析 3 件を実行・記録し、旧出力（`v5/outputs/sok_audit/rope_theta_ablation_summary.md`, `v5/outputs/sok_math_alpaca/`）は削除せず `INDEX.md` の「旧形式」に `置き換え済み` として記録した。
2. **`rope_theta` 比較表の改訂 (`20261126-1344_rope-theta-ablation-summary`)**:
   - 結論を「`rope_theta` 修正は一部に効く（SST 結合 VRR `7.63% → 15.89%`、TA HB Cond.ASR `34.43% → 23.63%`）が、それだけでは崩壊を説明できない（語彙数 32,001 と事前学習系統の切り分けは未実施・1 点確認）」へ修正。
   - HumanEval / MBPP / Code Avg 列すべてに「暫定」を明記し、結合 VRR・従来 VRR・拡張単独 VRR を併記。
3. **新 GSM8K × 安全性 3 判定器別・結合 VRR ≥ 90% 集計 (`20261126-1344_math-alpaca-analysis-interim`, `120/138`)**:
   - HarmBench / WildGuard / StrongREJECT の 3 判定器それぞれで線形補間表（「到達せず」明示）とペアードブートストラップ 95% CI を独立出力し、判定器による結論差（P2 実例）を定量化。
   - 結合 VRR ≥ 90% 下限へ統一し、参照点 3 種（Base / SafetyFT / WizardMath-7B）を図に描画、Pareto 図のタイトル切れも修正して目視確認済み。
4. **最優先 #2: LED-Merging 重み退化監査 (`20261126-1344_led-merging-weight-audit`)**:
   - 全 6 モデル（`safety+math`・`safety+code` × seed 42–44）で **`0 / 291` テンソル更新（`Llama-2-7b-hf` と 100.00% 一致、`proj_util = 0.00%`、`proj_safe = 0.00%`）** の完全退化を検出。
   - 根本原因を 2 重サイレントスキップと特定:
     - ① `locate/main.py --prune_method wandg --dump_wanda_score` が 289 層スコアを `random_score/` に出力したのに、`merging_methods.py` の `SCORE_BOOK` は `wanda_score/`（2 ファイルのみ）しか読まず 289/291 テンソルをサイレントスキップ。
     - ② 残り 2 テンソル（`embed_tokens`, `lm_head`）も語彙数 `32,000` vs `32,001` の不一致で `mask_weights_utils.py:576` によりサイレントスキップ。
5. **最優先 #1: WizardCoder HumanEval 崩壊の原因特定＋検証ゲート準備**:
   - `v3` で WizardCoder 単体の HumanEval が `5.49%`（MBPP `36.56%`、Avg `21.03%`）だった原因を、`### Instruction:` ラップで完全な `def` を再生成させた応答に `lm-eval` が `prompt + resp` を重複連結・`def` で切断していたことと特定。
   - `v5/configs/expert_eval_spec.yaml`、`v5/scripts/eval_code_wizardcoder_official.py`、`v5/scripts/run_wizardcoder_verify.sh` を整備し、空き GPU（`iag-03` GPU 2 等）で即実行可能な状態とした。

## 2. 検証結果
- `CUDA_VISIBLE_DEVICES="" /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/pytest /mnt/nas/home/hiromi/src/sst_v2/v5/tests -q`: **66 passed, 0 failed**。
- `git status --short -- v3/scripts v3/results v1 v2`: 差分ゼロ（NFR2 遵守）。
