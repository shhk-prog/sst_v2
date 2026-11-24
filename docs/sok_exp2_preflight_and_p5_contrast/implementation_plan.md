# 実装計画: SoK 実証 2 投入前検証・対照設計・P5 対照監査

## 目的
SoK 実証 2（`safety+math` の fp32 SST-Merge 再マージ＋GPU 評価）を SLURM に投入する前に、以下 6 点を厳密に整備・検証し、「P5 修正のみを変えた 1 要因比較」および「同一リポジトリ内での P5 対照証拠」を盤石にする。

## 変更・追加ファイル（すべて `v5/` 配下、`v3/` は読み取り専用）

1. **`v5/scripts/merge_fp32_sst_math.py`（改修）**
   - **② モデル–FIM キー・形状一致検証 (`verify_model_fim_alignment`)**:
     `Llama-2-7b-hf` の safetensors ヘッダから全 224 対象パラメータ名・形状を取得し、`F_h`・`F_b` 両 FIM キャッシュおよび `WizardMath-7B-V1.0` に欠落・形状不一致が 0 件であることを事前 assert する（`v3/scripts/mergers/fim.py` の `get_fim_tensor` による黙殺 0 返却経路を遮断）。
   - **③ 1 要因同等性テスト (`--mask-mode {fp32,v3}`, `--verify-v3-equivalence`)**:
     `--mask-mode v3` で `v3/scripts/mergers/sst.py` と同一の fp16 キャスト＋`>= threshold` マスクを再現し、`seed=42, α=0.6` の既存 `v3` モデル（`sst_merge_v3_main_diagonal_sst_main_safety+math_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42`）と全 291 テンソルを比較して `max_abs_diff == 0.0` を確認する。

2. **`v5/scripts/verify_fp32_merged_models.py`（新規）**
   - マージ直後に CPU 上で数分で実行し、以下 4 点を自動検証して `v5/outputs/sok_exp2/post_merge_verification_seed{seed}.{json,md}` に記録する（不合格時は非 0 終了し GPU 評価へ進まない）:
     1. `α=0.0` モデル vs `WizardMath-7B-V1.0`: `embed_tokens` / `lm_head` 以外の全 289 テンソルで `max_abs_diff == 0.0`（および語彙層 2 テンソルがベースモデルと一致）。
     2. `α=1.0` モデルの全 224 対象テンソル: 安全モデル側に置き換わった座標割合が `0.20 ± 0.05`。
     3. `α=0.6` モデルの対 `v3` TA 安全注入量比（V5 同一指標）: 中央値が `1.000`（v3）から `0.20` 付近（`< 0.50`）へ低下。
     4. `config.json` 比較: `rope_theta=10000.0`・`rms_norm_eps=1e-05` 等に P4 汚染がないこと、および `v3` と同一のベース継承仕様であること。

3. **`v5/scripts/slurm_fp32_sst_math.sh`（更新）**
   - Step 1（fp32 マージ）直後に Step 1b（`verify_fp32_merged_models.py`）を組み込み。
   - `seed=42`（`SLURM_ARRAY_TASK_ID == 0`）の Step 4 として、同 GPU 上で既存 `v3` 対照モデル 2 本（`task_arithmetic` α=0.6、`diagonal_sst_main` α=0.6）を再評価し `v5/results/fp32_sst_math/controls_seed42/` に保存。

4. **`v5/scripts/analyze_sok_exp2.py`（新規）**
   - `fp16 SST (v3)`・`fp32 SST (v5)`・`Task Arithmetic (v3)` を実証 1 の拡張妥当性ルールで統一集計。
   - 3 種の有害分類器（HarmBench / WildGuard / StrongREJECT）を個別集計し、`fp32` JSON の `classifier_output` 存在も検証。
   - 主図（横軸 Math %、縦軸 Conditional ASR %、3 seed mean ± std、3 分類器別パネルの曲線比較）と補助図（横軸 実効安全注入スケール）を生成。
   - プロンプト単位ブートストラップ（1,000 回、seed=20261124）で 95% CI を算出し、「P5 を直したとき曲線がどう動くか」として報告。
   - `controls_seed42` と元 `v3` 結果の GPU ドリフト比較表を出力。

5. **`v5/scripts/check_datafree_degeneration.py`（新規）**
   - CPU 上で `v3/scripts/mergers/sst.py` L150–181 の `data_free_sst`（fp16 `delta**2` + `>= threshold`）の桁落ち・全 1 マスク退化率を実測。
   - `v3/scripts/merging/matena_fisher.py`（fp32 演算・グローバル L2 正規化・連続重み）および `diagonal_sst` / `fisher_weighted` との 4 実装 P5 対照表を `v5/outputs/sok_audit/p5_method_contrast.md` に出力。

6. **`v5/tests/test_sok_exp2.py`（新規）**
   - `compute_mask_for_tensor`・拡張妥当性/分類器存在確認・Math 抽出・ブートストラップ・`rope_theta` 抽出の単体テストを追加。

## 検証計画
- `merge_fp32_sst_math.py --verify-mask-only`（② 整合性＋全 672 テンソル実効マスク検証）
- `merge_fp32_sst_math.py --verify-v3-equivalence`（③ 全 291 テンソル `max_abs_diff == 0.0`）
- `check_datafree_degeneration.py`（⑥ Data-Free SST 実測＋対照表生成）
- `analyze_sok_exp2.py` 既存 `v3` データでのドライラン実行
- `pytest v5/tests -q` および `git status --short -- v3 v1 v2` による NFR2 非改変確認
