# 実装計画：SoK 実証2（fp32 再マージ＋評価）・実証1（拡張妥当性再集計＋200件人手抽出）・外部コード監査

## 実行優先順
1. **最優先：実証2（`safety+math` の fp32 再マージ＋SLURM GPU ジョブ投入）**
   - `v5/scripts/merge_fp32_sst_math.py`:
     - `v3/scripts/mergers/sst.py` と `norm` 層・対象外パラメータ・語彙不一致（`embed_tokens`/`lm_head`）・`interpolation` 式・保存 config/tokenizer を完全一致させる。
     - 変更点は P5 に関わる 2 点のみ：(1) `v3/cache/fim/` の fp32 FIM を fp32 のまま $\lambda = F_h / (F_b + 10^{-6})$ 計算、(2) ハードマスクを `>= threshold` ではなく `torch.topk(..., k_elements).indices` で厳密に $k$ 個選択。
     - 各マージごとに全 224 テンソルの実効マスク比率・`inf` 数・`nan` 数・fp32 ゼロ率を `merge_metadata.json` に記録し、全テンソルで $|r - 0.20| \le 0.05$ を assert で検証。
     - `--verify-mask-only` で全 3 seed（42, 43, 44）のマスク比率を事前検証してから SLURM 投入。
   - `v5/scripts/slurm_fp32_sst_math.sh`:
     - Array job（seed 42, 43, 44 × $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$、計 18 モデル）。
     - 各モデルを `v5/models/fp32_sst_math/` にマージ → `v3/scripts/eval/eval_safety.py`（4 ベンチ・`--limit 320 --use_vllm`）→ `v3/scripts/eval/eval_utility.py`（`gsm8k,minerva_math500`・`--limit 320 --use_vllm`）→ `v3/scripts/tools/reclassify_safety_with_harmbench.py`（`--update_primary_asr`）を実行し、結果を `v5/results/fp32_sst_math/` に保存。
2. **並行：実証1（拡張妥当性判定の当て直し＋人手 200 件抽出、GPU 不要）**
   - `v5/scripts/sok_exp1_reval.py`:
     - `v3/results/vllm/debug_limit320` の全パターン・全 $\alpha$・全手法について、修正前（現行 `is_gibberish`）と修正後（現行ルール OR 非 ASCII 混入 OR 無空白長文字列）の VRR・VSR・Conditional ASR（HarmBench 単独 & ベンチマーク別）・手法順位を比較し、`v5/outputs/sok_exp1/` に Markdown 表・JSON・比較図を出力。
     - 人手判定 200 件を層化サンプリング（4 パターン・崩壊疑い有無・分類器一致/乖離を均衡抽出、固定 seed=20261124）し、ブラインド評価用 CSV（`human_eval_200_blind.csv`）と照合キー（`human_eval_200_key.json`）を出力。
3. **次：外部コード（`v3/baselines/`）の P1〜P5 監査**
   - `SafeMERGE`・`LED-Merging`・`MergeAlign`・`mergekit` のソースを先入観なく読み、P1〜P5 に対応する実装事実を行番号付きで `v5/outputs/sok_audit/external_code_audit.md` に記録する（問題が見つからない場合は「問題なし／報告なし」と正直に記載）。

## 制約
- `v3/` の既存ファイル・結果・モデル・キャッシュは一切変更しない（NFR2）。出力はすべて `v5/` 配下（および本計画書フォルダ）。
