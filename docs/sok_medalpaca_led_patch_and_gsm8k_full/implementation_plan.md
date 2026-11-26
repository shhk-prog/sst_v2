# 実装計画: MedAlpaca 検証準備・LED-Merging 非侵襲パッチ・GSM8K 全 1,319 問ランチャー

## 1. 目的
`iag-03` 上で GPU 1（数学 `seed 44`）および GPU 2（表 3＋`rope_theta` HumanEval 33 本）が稼働している間に、CPU 上で完結できる次の 3 準備を完了させる。

1. **MedAlpaca-7B 公式評価検証ゲート（§2.5 #3）**:
   - `GBaker/MedQA-USMLE-4-options-hf`（ローカルキャッシュ済み）を用いて `Llama-2-7b-hf` / `SafetyFT_seed42` / `medalpaca/medalpaca-7b` を公式 `Context / Question / Answer:` 形式（＋対照 `plain_qa`）で評価し、自動ゲートと全文 20 件目視表を出力する。
2. **LED-Merging 非侵襲最小パッチ（§4.2 + `PATCHES.md` + パッチ前後テスト）**:
   - 上流 `v3/baselines/LED-Merging/` は一切直接編集せず、`v5/scripts/led_merging_patched.py` の実行時モンキーパッチで `prune_wandg` の `_random_prune_core` → `_prune_core(prune_mode="gradient")` 1 行修正＋語彙数 32,000 vs 32,001 アライメントを適用する。
   - 差分と理由を `v5/PATCHES.md` に記録し、`v5/tests/test_led_merging_patch.py` でパッチ前（0 更新・ベース完全一致）とパッチ後（全層スコア一致・更新テンソル > 0・`proj_util > 10%`）を自動検証する。
3. **GSM8K 全 1,319 問評価ランチャー（§2.5 #4・§4.3）**:
   - 論文のブートストラップ主張点（`fp32_sst` α=0.8/1.0、`fp16_sst` α=0.8/1.0、`TA` α=0.6/0.8、`DARE` α=0.6 × 3 seed ＋単体 3 本 = 24 本）を固定済み `eval_math_alpaca_cot.py --limit 1319` で再評価するランチャーを整備する。

## 2. 制約
- `v3/`・`v1/`・`v2/` は完全に読み取り専用（NFR2）。
- すべての実行ランチャーは `--run-dir`（`RUN.md` 存在必須）を要求する（指示書 v2 §1.4）。
