# PATCHES.md — 上流リポジトリに対する最小修正およびゲート既定値の根拠記録（sst_v2/v5）

指示書 v2 §4.4・§6 に準拠し、上流実装の挙動修正と設計判断の根拠をここに記録する。
**制約**: `v3/` 配下の上流リポジトリ（`v3/baselines/LED-Merging/` 等）は一切直接書き換えず、すべてのパッチは `v5/scripts/` 側の実行時ラッパーとして最小差分で適用する。

---

## 1. LED-Merging (`MqLeet/LED-Merging`, commit `1149224f17e1af020d1205ed5367b033e5f030fe`)

### 1.1 観測された現象（`20261126-1344_led-merging-weight-audit`）
- 公開コード（commit `1149224`）を公式 README・`locate/scripts/locate_inst.sh` どおりの引数（`--prune_method wandg --sparsity_ratio 0.01 --sparsity_type unstructured --neg_prune --dump_wanda_score`）でそのまま実行したところ、`v3` の LED-Merging 全 6 モデル（`safety+math`・`safety+code` × seed 42, 43, 44）が **`0 / 291` テンソル更新（`Llama-2-7b-hf` ベースと 100.00% 一致、`rel_diff_vs_base = 0.0000%`, `proj_util = 0.00%`）** で終了コード 0（`status: "success"`）となった。
- 上流 GitHub Issue（2026-11-26 時点、全 3 件）を確認したが、本現象は未報告だった。

### 1.2 根本原因（2 点）
1. **原因 A（`locate/lib/model_wrapper.py`, `def prune_wandg`, L516–533、未改変上流コード）**:
   本来 289 個の Transformer 層スコアを `wanda_score/` へ書き出す `_prune_core(...)` がコメントアウトされたままになっており、代わりに `torch.randperm` による乱数マスクを `random_score/` へ書き出す `_random_prune_core(...)` が呼び出されていた。その結果、`wanda_score/` には `embed_tokens.pkl` と `lm_head.pkl` の 2 ファイルしか保存されず、マージ側 `SCORE_BOOK`（`wanda_score/` を参照）が残り 289 テンソルすべてを警告なしでベース重みへフォールバックした。
2. **原因 B（`model_merging_methods/mask_weights_utils.py`, `def neuron_merge_weight`, L569–586）**:
   残る 2 テンソル（`embed_tokens.weight`, `lm_head.weight`）も、ベース（語彙数 `32,000`）と拡張済み入力モデル（`32,001`）の形状不一致（`[32000, 4096]` vs `[32001, 4096]`）で `if true_mask.shape != sft_param[param_name].shape: continue` により警告なしでスキップされた。

### 1.3 最小パッチ差分（実行時ラッパー `v5/scripts/led_merging_patched.py` で適用、上流ファイル非改変）

#### (a) 1 行修正：`locate/lib/model_wrapper.py` L516–533（重要度保存の有効化）
```diff
--- a/locate/lib/model_wrapper.py
+++ b/locate/lib/model_wrapper.py
@@ -516,18 +516,11 @@ def prune_wandg(
-        # _prune_core(
-        #     args,
-        #     model,
-        #     model_base,
-        #     prune_n,
-        #     prune_m,
-        #     prune_mode="activation", # "gradient", # for snip
-        #     name_filter_fn=layer_filter_fn,
-        # )
-        _random_prune_core(
+        _prune_core(
             args,
             model,
             model_base,
             prune_n,
             prune_m,
+            prune_mode="gradient",
             name_filter_fn=layer_filter_fn,
         )
```
- **理由**: `prune_wandg`（L453）は `with no_act_recording(model):` で勾配絶対値 `module.base.weight.grad.abs()` を積算するため、Equation 1 の重要度 $|W \odot \nabla L|$ を `wanda_score/` に保存するには `_prune_core(..., prune_mode="gradient")` を呼ぶ必要がある。なお `_prune_core`（L598）は `neg_prune=True` のとき `-W_metric`（負値）を保存するが、`embed_tokens` / `lm_head`（L494, L507）および `mask_weights_utils.py`（L534, `descending=True`）は正の重要度の降順上位を選択するため、ラッパーでは `neg_prune=False` で正値 $|W \odot \nabla L|$ を保存し符号を整合させている。

#### (b) 語彙数アライメント修正（`v5/scripts/led_merging_patched.py` 側での安全適用）
- ベース語彙 `32,000` と SFT 語彙 `32,001` の差分行（末尾 1 行 `[PAD]`）について、先頭 `min0 = 32,000` 行には `true_mask` を適用し、末尾の拡張行は SFT 側を維持（または 0 マスク埋め）することで、2 テンソルの無警告スキップを防ぐ。
- さらにラッパー側で以下を必須ゲート検証する：
  1. スコアファイル数が対象テンソル数と一致すること（欠落時は即エラー終了）。
  2. マージ後に単精度 §4.2 監査を実行し、更新テンソル数 `> 0`・`rel_diff_vs_base >= 1%`・`proj_util >= 10%` を確認すること。

### 1.4 検証テスト
- `v5/tests/test_led_merging_patch.py`: パッチ前（`wanda_score/` 2 ファイル＋語彙不一致）で `0` テンソル更新・ベース完全一致になること、パッチ後（`_prune_core`＋語彙アライメント）でスコアファイル数一致・更新テンソル数 `> 0`・`proj_util > 0` になることを自動検証。
- 論文での表記:
  - `v3` 実環境トラック表: 公開コード（commit `1149224`）そのままの結果は「退化（未マージ・ベースモデル）」と注記。
  - パッチ適用後の `safety+math`（seed 42）1 点再実行結果: 「公開コードに最小の修正（`_prune_core` 有効化）を加えて実行」と注記。

---

## 2. 完全性ゲートの厳しさの根拠（指示書 v2 §4.4）

- **根拠実験フォルダ**:
  - `v5/results/runs/20261126-1239_rope-theta-ablation-eval`
  - `v5/results/runs/20261126-1344_rope-theta-ablation-summary`
- **結論の範囲**: `safety+code`（`α=0.6, seed42`）で `rope_theta` のみ `10,000 → 1,000,000` に修正した結果、SST の結合 VRR は `7.63% → 15.89%`、TA の HarmBench 条件付き ASR は `34.43% → 23.63%` と一部に効果が見られたものの、DARE（結合 VRR `0.32%`）・SST（`15.89%`）の崩壊は止まらず、「設定の取り違え（`rope_theta`）だけでは崩壊を説明できない」ことが確かめられた（語彙数 32,001 と事前学習系統の切り分けは未実施・1 点確認）。
- **ゲート既定値**: 層別相対差分の中央値 `> 50%`（系統不一致）は不合格、設定不一致（`rope_theta`, `vocab_size`, `eos_token`, chat template）は警告とする。
