# タスクリスト: MedAlpaca 検証準備・LED-Merging 非侵襲パッチ＋前後テスト・GSM8K 全 1,319 問ランチャー

## 完了済みタスク
- [x] **MedAlpaca-7B 公式医療評価検証ゲート準備（指示書 v2 §2.5 #3）**
  - `v3` の医療評価結果を確認（`MedQA-4options`: MedAlpaca `31.88%` vs SafetyFT `29.06%`、`PubMedQA`: MedAlpaca `73.75%` vs SafetyFT `84.38%`、`MedAlpaca-7B` は Llama-1 ベース・`vocab_size=32001`）
  - `v5/scripts/eval_medical_medalpaca_official.py`（公式 `Context / Question / Answer:` 形式＋対照 `plain_qa`、全応答保存・A/B/C/D 抽出・自動ゲート・省略なし 20 件目視表）と `v5/scripts/run_medalpaca_verify.sh` を作成
- [x] **LED-Merging 非侵襲最小パッチ＋`PATCHES.md`＋前後比較テスト**
  - 上流 `v3/baselines/LED-Merging/` を 1 文字も変更せず、実行時メモリ上で `locate/lib/model_wrapper.py` の `_random_prune_core` → `_prune_core(prune_mode="gradient")` へ差し替えるラッパー `v5/scripts/led_merging_patched.py` と 1 点再実行ランチャー `v5/scripts/run_led_merging_math_seed42.sh` を作成
  - 1 行差分・理由・完全性ゲート §4.4 根拠を `v5/PATCHES.md` に記録
  - `v5/tests/test_led_merging_patch.py` で「パッチ前は 0 テンソル更新・ベース完全一致（退化）、パッチ後は全層スコア揃い・更新テンソル > 0・`proj_util > 10%`」を自動検証
- [x] **GSM8K 全 1,319 問評価ランチャー準備（指示書 v2 §2.5 #4・§4.3）**
  - 主要点（単体 3 本＋`fp32_sst α=0.8/1.0`, `fp16_sst α=0.8/1.0`, `TA α=0.6/0.8`, `DARE α=0.6` × 3 seed = 計 24 本）の `v5/scripts/run_math_gsm8k_full1319.sh` を作成
- [x] `pytest v5/tests -q` 全 **69 passed**、NFR2（`v3/`・`v1/`・`v2/` 非改変）確認

## 残タスク（GPU 完了待ち・16:20 ごろ〜）
- [ ] `seed 44`（現在 38/46）完了後、新フォルダで数学最終集計（`138/138`）を実行し、中間版を「置き換え済み」に更新
- [ ] GPU 1 空き次第、`run_math_gsm8k_full1319.sh`（主要点 24 本 × GSM8K 1,319 問）を実行
- [ ] コード 33 本完了後、`rope_theta` 比較表・表 3 の HumanEval 確定集計を作成し、空き GPU で `run_medalpaca_verify.sh` および `run_led_merging_math_seed42.sh` を実行
