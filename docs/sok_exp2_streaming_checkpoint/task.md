# タスクリスト: SoK 実証 2 全フェーズの 1 件ずつ逐次保存・途中再開対応

- [x] `v3` 既存評価スクリプト 3 本（`eval_safety.py`, `eval_utility.py`, `reclassify_safety_with_harmbench.py`）の保存粒度を監査
- [x] `v5/scripts/eval_safety_streaming.py` の作成（vLLM/HF 生成・分類とも 1 件ごと原子保存、空応答・全既存フィールド保持再開）
- [x] `v5/scripts/eval_utility_streaming.py` の作成（lm-eval の `generate_until` / `loglikelihood` を 1 件ごと JSONL 追記＋`fsync`、途中再開・破損末尾行耐性）
- [x] `v5/scripts/reclassify_harmbench_streaming.py` の作成（HarmBench 13B 再分類を 1 件ごと原子保存、全件完了時のみトップレベル確定）
- [x] `v5/scripts/merge_fp32_sst_math.py` の `merge_metadata.json` 書き込みを原子保存化（`.tmp` + `fsync` + `os.replace`）
- [x] `v5/scripts/slurm_fp32_sst_math.sh` を全ステップ `v5` 逐次保存スクリプト経由に切り替え
- [x] 単体テスト `v5/tests/test_streaming_eval.py` の追加と全テスト・構文・NFR2（`v3/` 非改変）確認
