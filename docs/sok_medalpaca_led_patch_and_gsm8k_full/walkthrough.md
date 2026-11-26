# 修正内容の確認 (Walkthrough): MedAlpaca 検証準備・LED-Merging 非侵襲パッチ・GSM8K 全 1,319 問ランチャー

## 1. 作成・整備した成果物
1. **上流パッチ記録 (`v5/PATCHES.md`)**:
   - `MqLeet/LED-Merging` (commit `1149224`) の `locate/lib/model_wrapper.py` L516–533 の 1 行修正（`_random_prune_core` → `_prune_core(prune_mode="gradient")`）の unified diff と理由、語彙数 32,000 vs 32,001 アライメント、および §4.4 完全性ゲート既定値根拠（`20261126-1239_rope-theta-ablation-eval` / `20261126-1344_rope-theta-ablation-summary`）を記録。
2. **LED-Merging 非侵襲パッチラッパー＋ランチャー**:
   - `v5/scripts/led_merging_patched.py`: 上流ファイルを変更せずメモリ上で 1 行修正を適用し、スコアファイル数検証（`>= 224`）・語彙アライメント・Elect/Disjoint マージ・単精度 §4.2 退化監査（`updated_tensors > 0` 検証）を一貫実行。
   - `v5/scripts/run_led_merging_math_seed42.sh`: パッチ適用済み `safety+math (seed 42)` マージ → ロック済み GSM8K Alpaca-CoT (320 問) → 安全性 4 ベンチ＋HarmBench 公式分類器再分類を一括実行。
3. **LED-Merging パッチ前後回帰テスト (`v5/tests/test_led_merging_patch.py`)**:
   - 同一の合成モデル（base 語彙 16 vs SFT 語彙 17、Transformer 2 層）に対して、パッチ前は **`0` テンソル更新・ベース完全一致（`rel_diff_vs_base = 0.0%`, `degenerated=True`）**、パッチ後は **全テンソル更新・`rel_diff_vs_base > 1%`・`proj_util > 10%`（`degenerated=False`）** になることを検証。
   - 実行時モンキーパッチが `_prune_core(prune_mode="gradient")` へ正しくリダイレクトされ、終了後に復元されることも確認。
4. **MedAlpaca 公式医療評価検証ゲート**:
   - `v5/scripts/eval_medical_medalpaca_official.py` / `v5/scripts/run_medalpaca_verify.sh`: `GBaker/MedQA-USMLE-4-options-hf` で `official_qa` / `plain_qa` の 2 形式を評価し、全応答保存・A/B/C/D 抽出・自動ゲート・省略なし 20 件目視表を出力。
5. **GSM8K 全 1,319 問評価ランチャー**:
   - `v5/scripts/run_math_gsm8k_full1319.sh`: 主要点 24 本（単体 3 本＋7 条件 × 3 seed）をロック済み `eval_math_alpaca_cot.py --limit 1319` で途中再開対応付き実行。

## 2. 検証結果
- `CUDA_VISIBLE_DEVICES="" /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/pytest /mnt/nas/home/hiromi/src/sst_v2/v5/tests -q`: **69 passed, 0 failed**。
- `git status --short -- v3/scripts v3/results v1 v2`: 差分ゼロ（NFR2・上流非改変遵守）。
- 稼働中 GPU ジョブ進捗（15:27 JST 時点）:
  - GPU 1 数学 `seed 44`: **38 / 46**（残り 8 本、16:20 ごろ完了見込み）
  - GPU 2 コード 33 本 (`20261126-1518_code-table3-and-rope-humaneval`): **2 / 33** 完了・3 本目実行中
