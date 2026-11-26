# タスクリスト: コード表 3・`rope_theta` 確定集計およびバッチ推論・事前点検

- [x] `20261126-1709_math-gsm8k-full1319-keypoints` 起動失敗（`--output-json` 引数名ミス）の診断・修正と高速バッチ推論ラッパー `eval_math_alpaca_cot_batched.py` の実装・320/320 一致検証
- [x] `run_medalpaca_verify.sh` / `run_led_merging_math_seed42.sh` / `led_merging_patched.py` の事前点検・引数修正・`neg_prune=False` 符号整合修正・`PATCHES.md` 反映
- [x] `20261126-1518_code-table3-and-rope-humaneval` 全 33 本完了の確認・`RUN.md` / `INDEX.md` の完了更新
- [x] `v5/scripts/summarize_code_table3_and_rope_final.py` と単体テストの作成・検証
- [x] 新ランフォルダ `20261126-1740_code-table3-and-rope-summary-final` での表 3・`rope_theta` 確定集計の実行（未検証 MBPP 除外・暫定解消）
- [x] 旧 `20261126-1344_rope-theta-ablation-summary` および旧 `v3` コード有用性を `置き換え済み` に更新し、`v5/tests` 全テスト通過を確認
