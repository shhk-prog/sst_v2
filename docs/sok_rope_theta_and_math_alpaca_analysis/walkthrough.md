# 修正内容の確認 (Walkthrough): `rope_theta` 因果切り分け正式比較表 ＆ 新 GSM8K（Alpaca-CoT）× 安全性 最終集計

## 1. 実施した作業
1. **`rope_theta` 因果切り分け集計 (`v5/scripts/summarize_rope_theta_ablation.py`)**
   - 初回実行時に `v3` の SST 結果ディレクトリ名（`diagonal_sst_main`）を修正し、さらに第 4 節の結論数値をハードコードではなく計算済み辞書から動的生成する形へ改善した。
   - 出力:
     - `v5/outputs/sok_audit/rope_theta_ablation_summary.md`
     - `v5/outputs/sok_audit/rope_theta_ablation_summary.json`
2. **新 GSM8K（Alpaca-CoT）× 安全性 集計・プロット・ブートストラップ (`v5/scripts/analyze_math_alpaca_cot.py`)**
   - 完了済み `117 / 138` モデル（`seed 42`: 46/46、`seed 43`: 46/46、`seed 44`: 25/46、`fp32 SST` 全 18 本・`fp16 SST α=0.0–0.6` は既に `n=3`）を集計した。
   - 生成画像 3 枚を目視検査したところ、`math_alpaca_p5_curve_3classifiers.png` のタイトルと凡例の重なり、および `math_alpaca_all11_pareto.png` の右端ラベルはみ出しを検出したため、余白とアノテーション配置（引き出し線付きオフセット）を修正して再生成し、重なりゼロを確認した。
   - 出力:
     - `v5/outputs/sok_math_alpaca/math_alpaca_analysis.md` / `.json`
     - `v5/outputs/sok_math_alpaca/math_alpaca_p5_curve_3classifiers.png`
     - `v5/outputs/sok_math_alpaca/math_alpaca_all11_pareto.png`
     - `v5/outputs/sok_math_alpaca/math_prompt_before_after_alpha06.png`
3. **単体テスト追加 (`v5/tests/test_math_alpaca_cot.py`)**
   - `parse_alpaca_model_name`、`compute_pareto_front`（VRR ≥ 80% 制約・非劣解抽出）、`_extract_pass1` のテストを追加した。

## 2. 主要な定量結果

### (A) P4 `rope_theta` 因果切り分け（`safety+code, α=0.6, seed42`）
- **DARE**: 文字化け率 `100.00% → 99.68%`、拡張 VRR `0.00% → 0.32%`、Code Avg `0.00% → 0.00%`（完全崩壊のまま）。
- **fp16 SST (v3)**: 文字化け率 `91.36% → 81.50%`、拡張 VRR `7.63% → 15.89%`、Code Avg `0.00% → 0.00%`（わずかに非文字化け応答が増えたのみ、依然として崩壊）。
- **Task Arithmetic**: 拡張 VRR `92.83% → 92.03%`、Cond.ASR HB `34.43% → 23.63%`、Cond.ASR WG `74.58% → 65.09%`、Cond.ASR SR `68.62% → 69.97%`、Code Avg `4.53% → 3.59%`（HumanEval `0.00%`、MBPP `9.06% → 7.19%`）。
- **結論**: `safety+code` の文字化け・コード能力崩壊は `rope_theta` 取り違えだけでは説明できず、**異系統モデル（CodeLlama × Llama-2）の重み混合が主因**であることが確定した。

### (B) 新 GSM8K（Alpaca-CoT）× 安全性（現時点 `117/138`）
- 単体参照: **WizardMath-7B-V1.0 = `55.62%`**、**SafetyFT_seed42 = `7.50%`**、**Llama-2-7b-hf = `1.88%`**。
- **α=0.6 主結果**: `fp32 SST` **`52.71%`** (`n=3`) / `Data-Free SST` **`51.25%`** / `DARE` **`48.75%`** / `DELLA` **`48.44%`** / `fp16 SST` **`48.12%`** (`n=3`) / `TIES` **`46.72%`** / `Matena-Fisher` **`40.47%`** / `Task Arithmetic` **`32.34%`** / `SafeMERGE` **`5.31%`** / `LED-Merging` **`1.88%`** / `MergeAlign` **`0.00%`**。
- **同等安全性水準でのブートストラップ 95% CI**:
  - `HB=0%`（全 3 分類器 0.00%）: `fp16 SST (α=1.0)` − `TA (α=0.8)` = **`+16.72 pp [+12.03, +21.41]`**（有意）。
  - `HB~2–8%`: `fp32 SST (α=1.0)` − `TA (α=0.6)` = **`+14.81 pp [+10.16, +19.69]`**、`fp16 SST (α=0.8)` − `TA (α=0.6)` = **`+11.56 pp [+7.03, +15.62]`**（いずれも有意）。
  - `HB~15–17%` (`n=3`): `fp32 SST (α=0.8)` − `fp16 SST (α=0.6)` = **`+0.53 pp [-2.92, +3.96]`**（`Cond.ASR WG -4.51 pp [-7.72, -1.20]`、`SR -10.33 pp [-13.01, -7.49]` と安全性側は fp32 SST がやや低い）。

## 3. 検証結果
- `CUDA_VISIBLE_DEVICES="" /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/pytest /mnt/nas/home/hiromi/src/sst_v2/v5/tests -q`: **61 passed, 0 failed**。
- `git status --short -- v3/scripts v3/results v1 v2`: 差分ゼロ（NFR2 遵守）。
- `seed 44` 全 46 本完了後の 1 行再実行コマンド:
  `CUDA_VISIBLE_DEVICES="" /mnt/nas/home/hiromi/src/sst_v2/venv_sst/bin/python /mnt/nas/home/hiromi/src/sst_v2/v5/scripts/analyze_math_alpaca_cot.py`
