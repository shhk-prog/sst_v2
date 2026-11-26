# 修正内容の確認 (Walkthrough): コード表 3・`rope_theta` 確定集計および並行実験スクリプト点検

## 1. 確定集計（`20261126-1740_code-table3-and-rope-summary-final`）
- 作成・検証したスクリプト:
  - `v5/scripts/summarize_code_table3_and_rope_final.py`
  - `v5/tests/test_summarize_code_table3_and_rope_final.py`
- 生成ファイル:
  - `v5/results/runs/20261126-1740_code-table3-and-rope-summary-final/outputs/rope_theta_ablation_summary_final.md`
  - `v5/results/runs/20261126-1740_code-table3-and-rope-summary-final/outputs/code_table3_summary_final.md`
  - `v5/results/runs/20261126-1740_code-table3-and-rope-summary-final/outputs/code_table3_and_rope_summary_final.json`
  - `v5/results/runs/20261126-1740_code-table3-and-rope-summary-final/summary.json`

### 主な確定値
1. **`rope_theta` 切り分け確定比較（`α=0.6, seed42`, Before `10,000` → After `1,000,000`）**:
   - `Task Arithmetic`: 結合 VRR `92.83% → 92.03%`, HB Cond.ASR `34.43% → 23.63%`, WG `74.58% → 65.09%`, SR `68.62% → 69.97%`, HumanEval **`2.44% (4/164) → 4.27% (7/164)`**
   - `DARE`: 結合 VRR `0.00% → 0.32%`, HumanEval **`0.00% → 0.00%`**
   - `fp16 SST (v3)`: 結合 VRR `7.63% → 15.89%`, HumanEval **`0.00% → 0.00%`**（抽出失敗率 `18.29% → 12.20%`）
   - 結論範囲: 設定修正は一部に効くものの崩壊もコード能力喪失も止まらず、「設定の取り違え（`rope_theta`）だけでは崩壊を説明できない」（1 点確認、語彙数 32,001 と事前学習系統は未分離）。
2. **表 3 確定集計（`safety+code`, `α=0.6`, 10 手法 × 3 seed, WizardCoder 単体 `50.61%`）**:
   - `TIES / DARE / DELLA / Fisher Merging / fp16 SST / Data-Free SST / MergeAlign` の 7 手法は全 3 seed で HumanEval **`0.00%` (0/164)** かつ結合 VRR `< 90%` で失格。
   - `Task Arithmetic (α=0.6)`: 結合 VRR `94.27 ± 1.37%`（合格）, HumanEval **`4.47 ± 1.76%`** (`2.44 / 5.49 / 5.49%`), HB Cond.ASR `30.55 ± 3.46%`。
   - `SafeMERGE`: 結合 VRR `99.92 ± 0.14%`（合格）, HumanEval **`5.69 ± 5.50%`** (`10.98 / 6.10 / 0.00%`, seed 間で崩壊不安定), HB Cond.ASR `0.10 ± 0.18%`。
   - `LED-Merging† (v3)`: 3 seed とも **`2.44 ± 0.00%` (4/164)** で `Llama-2-7b-hf` ベース単体と 100% 一致（0/291 テンソル更新の退化をコード側でも裏付け）。

## 2. 並行実験スクリプトの修正・検証
- `v5/scripts/run_math_gsm8k_full1319.sh`: `--output-json` → `--output-file` 修正、およびロック済み `eval_math_alpaca_cot.py`（SHA256 不変検証）を import する `--batched` 版（`v5/scripts/eval_math_alpaca_cot_batched.py`）を追加。WizardMath 先頭 320 問はロック済み逐次版と **320/320 正誤 100% 一致**（全 1,319 問 `54.66%` [721/1319]）。
- `v5/scripts/run_led_merging_math_seed42.sh` / `v5/scripts/led_merging_patched.py`: 評価 3 コマンドの引数修正と `neg_prune=False`（正値重要度と降順選択の符号整合）を適用し、`v5/PATCHES.md` に記録。
- `v5/results/runs/INDEX.md` および各 `RUN.md`: 完了・置き換え済み状態を反映。
