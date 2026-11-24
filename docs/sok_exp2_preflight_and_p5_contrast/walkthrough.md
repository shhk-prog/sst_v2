# 修正内容の確認 (Walkthrough): SoK 実証 2 投入前検証・対照設計・P5 対照監査

## 1. 投入前修正・CPU 事前検証の結果

### ①② モデル–FIM キー・形状一致検証＋fp32 マスク検証 (`v5/scripts/merge_fp32_sst_math.py`)
- `Llama-2-7b-hf`（ベースモデル）の全 224 対象パラメータ（`q/k/v/o/gate/up/down_proj` の `weight`）の名前と形状が、`F_h`・`F_b` 両方の FIM キャッシュおよび `WizardMath-7B-V1.0` に 100% 一致することを事前 assert で保証した（`v3/scripts/mergers/fim.py` `get_fim_tensor` の欠落キー黙殺 0 返却経路を遮断）。
- 同時に、HF キャッシュ解決関数を `refs/main` 優先＋全シャード実在確認付きに修正し、`WizardMath` の不完全スナップショット誤選択も防止した。
- **CPU 実行結果**（`v5/outputs/sok_exp2/mask_preflight_verify.json`）:
  - `seed=42, 43, 44` すべてで `target=224/224, missing_fh=0, missing_fb=0, shape_mismatch=0`
  - 全 672 テンソルの実効マスク比率: `mean=0.200000`, `range=[0.200000, 0.200000]`, `inf=0`, `nan=0`

### ③ 1 要因同等性テスト (`--mask-mode v3` / `--verify-v3-equivalence`)
- `seed=42, α=0.6` について、既存の `v3` マージ済みモデル（`sst_merge_v3_main_diagonal_sst_main_safety+math_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42`）の全 291 テンソル（非永続バッファ `rotary_emb.inv_freq` を除く全 6,738,415,616 パラメータ）と照合した（`v5/outputs/sok_exp2/v3_equivalence_check.json`）。
- **結果**:
  - 保存済み GPU 生成 `v3` モデルとの比較: **286 / 291 テンソルが完全一致（差 `0.0`）**。残り 5 テンソル計 **12 要素**（全パラメータの $1.78 \times 10^{-9}$, `max_abs_diff = 3.11e-4`）は fp16 除算 `f_h / (f_b + 1e-6)` の CUDA vs CPU 1 ULP 境界差に起因。
  - その 5 テンソルを同一 CPU プロセス内で `v3/scripts/mergers/sst.py` の `merge_sst()` と直接照合したところ、**全 5 テンソルで差 `0.0`** を確認。
  - これにより、`fp32` 版との差分は **P5（fp32 λ 計算＋インデックス top-k マスク）の 1 要因のみ**であることが確認できた。

---

## 2. マージ直後検証・GPU 対照モデル・評価後解析の整備

- **マージ直後 CPU 検証 (`v5/scripts/verify_fp32_merged_models.py`)**:
  1. `α=0.0` vs `WizardMath-7B-V1.0`: `embed_tokens` / `lm_head` 以外の全 289 テンソルで `max_abs_diff == 0.0`（語彙層 2 テンソルはベースモデルと一致）
  2. `α=1.0` の全 224 対象テンソル: 安全モデル側へ置き換わった座標割合が `0.20 ± 0.05`
  3. `α=0.6` の対 `v3` TA 安全注入量比（V5 同一指標）: 中央値が `v3` の `1.000` から `0.20` 付近（`< 0.50`）へ低下
  4. `config.json`: `rope_theta=10000.0`, `rms_norm_eps=1e-05` 等が `WizardMath-7B-V1.0` と一致（P4 汚染なし）
- **SLURM ジョブ (`v5/scripts/slurm_fp32_sst_math.sh`)**:
  - Step 1（fp32 マージ）直後に Step 1b（`verify_fp32_merged_models.py`）を実行し、異常があれば GPU 評価前に即中止。
  - `seed=42`（`SLURM_ARRAY_TASK_ID == 0`）に Step 4 を追加し、GPU 差の対照として既存 `v3` モデル 2 本（`task_arithmetic` α=0.6、`diagonal_sst_main` α=0.6）を同一 GPU で再評価し `v5/results/fp32_sst_math/controls_seed42/` に保存。
- **評価後解析・プロット (`v5/scripts/analyze_sok_exp2.py`)**:
  - 実証 1 の拡張妥当性判定を全 3 手法（`fp32 SST`, `fp16 SST`, `TA`）に統一適用し、HarmBench・WildGuard・StrongREJECT の 3 分類器を個別集計。
  - `fp32` JSON の `classifier_output` / `harmbench_cls_output` 欠落チェック、主図（横軸 Math %、縦軸 Conditional ASR %、3 seed mean ± std、3 分類器別パネル）、補助図（横軸 実効安全注入スケール）、プロンプト単位ブートストラップ（1,000 回、95% CI）、GPU 対照ドリフト表を出力。
  - 既存 `v3` 結果でのドライラン（`v5/outputs/sok_exp2/dryrun_v3_baseline/`）がエラーなく完了することを確認済み。

---

## 3. P5 対照監査: Data-Free SST vs Diagonal SST vs Matena-Fisher

CPU 実測スクリプト `v5/scripts/check_datafree_degeneration.py` を実行し、`v5/outputs/sok_audit/datafree_degeneration.json` および `v5/outputs/sok_audit/p5_method_contrast.md` を生成した。

- **Data-Free SST（`v3/scripts/mergers/sst.py` L150–181）の CPU 実測**:
  - `phi_h = delta_safe ** 2` を fp16 のまま計算するため、`phi_h == 0` 率が fp32 の **2.58%** から fp16 で **65.25%**（`safety+math` 3 seed 平均）へ急増。
  - その結果、`>= threshold` により全 224 対象テンソル中 **26〜28 テンソル（11.6〜12.5%）が全 1 マスクへ退化**、実効マスク平均も `0.200` → **`0.303〜0.311`** に膨張した（`safety+code`, `safety+medical` でも同じく 27/224 = 12.1% が全 1）。
- **Matena-Fisher（`v3/scripts/merging/matena_fisher.py` L48–54, L140–171）**:
  - 同じ fp32 FIM キャッシュを入力としながら、`numerator`/`denominator`/`theta_i`/`f_i` を明示的に **fp32** で計算し、グローバル L2 正規化＋`clamp(min=1e-6)` を行い、保存直前（L171）のみ fp16 に戻しているため P5 は構造的に発生しない。
- **同一リポジトリ内の 3 段階対照**: `diagonal_sst`（重度 P5: 60.4% 全 1） / `data_free_sst`（中度 P5: 12.1% 全 1） / `matena_fisher`（P5 なし: 0%）。

---

## 4. テスト・安全確認
- `pytest v5/tests -q`: **55 passed**（新規 `v5/tests/test_sok_exp2.py` 5 件含む）
- `bash -n v5/scripts/slurm_fp32_sst_math.sh` / `py_compile`: すべて異常なし
- NFR2: `v3/`・`v1/`・`v2/` への書き込みゼロ（読み取り専用維持）
- SLURM ジョブは未投入（実行コマンドをユーザーへ提示済み）
