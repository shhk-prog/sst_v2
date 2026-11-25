# 実装計画: SoK 実証 2 全フェーズの 1 件ずつ逐次保存・途中再開対応

## 監査で判明した従来（`v3`）の課題
1. `v3/scripts/eval/eval_safety.py`: 分類は 1 件ごと保存していたが、**`--use_vllm` の生成フェーズは 320 件まとめて推論後に 1 回だけ保存**だった。
2. `v3/scripts/eval/eval_utility.py`: **`lm_eval.simple_evaluate` が 640 件（GSM8K 320 + Minerva500 320）をすべて推論し終えてから最後に 1 回だけ保存**だった。
3. `v3/scripts/tools/reclassify_safety_with_harmbench.py`: **全ファイル・全サンプル（最大 7,680 件）をまとめて推論した後に最後に一括保存**だった。

## 対応方針（`v3/` は完全読み取り専用を維持し、すべて `v5/scripts/` に実装）
1. **`v5/scripts/eval_safety_streaming.py`**:
   - 生成（vLLM / HF 共通）を 1 件ずつ実行し、1 件ごとに `save_checkpoint`（`.tmp` -> `os.replace`）を実行。
   - 再開時に空文字応答 `""` や既存の `harmbench_cls_*` / `original_asr` / `is_gibberish` を落とさず保持。
   - 分類フェーズも 1 件ごとに原子保存。
2. **`v5/scripts/eval_utility_streaming.py`**:
   - `lm_eval` の `lm_obj`（`VLLM` / `HFLM`）の `generate_until`・`loglikelihood`・`loglikelihood_rolling` をラップし、**1 件推論するごとに `<output_file>.stream.jsonl` へ 1 行追記＋`flush()`＋`os.fsync()`**。
   - 再実行時はキャッシュ JSONL から完了済み件数を即座に復元し、未推論の 1 件目から再開（末尾破損行も安全に無視）。プロンプト・採点・`fix_gsm8k_jsons_fast.py` は `v3` と完全同一。
3. **`v5/scripts/reclassify_harmbench_streaming.py`**:
   - HarmBench 13B 分類器で 1 件ずつ推論し、**1 件ごとに JSON ファイルを原子保存（`.tmp` + `fsync` + `os.replace`）**。
   - 全件完了時のみトップレベル `harmbench_cls_asr` を確定させることで、途中再開時の誤スキップを防止。
4. **`v5/scripts/merge_fp32_sst_math.py`**:
   - `merge_metadata.json` の保存を `.tmp` + `fsync` + `os.replace` の原子保存に変更。
5. **`v5/scripts/slurm_fp32_sst_math.sh`**:
   - Step 2a/2b/3 および Step 4a/4b/4c（対照 2 本）をすべて上記 3 本の `v5` 逐次保存スクリプトへ切り替え。
