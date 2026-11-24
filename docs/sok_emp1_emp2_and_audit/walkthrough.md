# 修正内容の確認（Walkthrough）：SoK 実証2（GPU投入）・実証1（再集計＋人手200件）・外部コード監査

## 1. 実証 2：`safety+math` fp32 SST 再マージと SLURM GPU ジョブ投入（最優先完了）
- **スクリプト作成**:
  - [merge_fp32_sst_math.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/merge_fp32_sst_math.py):
    - `v3/scripts/mergers/sst.py` と `norm` 層（L103-105）・語彙不一致 `embed_tokens`/`lm_head`（L53-55）・`interpolation` 式（L191-192）・保存 config/tokenizer を完全同一に保ち、P5 に関わる 2 点（fp32 FIM/λ 計算・`torch.topk(...).indices` による厳密 top-k マスク）のみを修正。
    - 全 224 対象テンソルの実効マスク比率・`inf`・`nan`・fp32 ゼロ率を `merge_metadata.json` に記録し、$|r - 0.20| \le 0.05$ かつ `inf=0, nan=0` を assert で検証。
  - [slurm_fp32_sst_math.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/slurm_fp32_sst_math.sh):
    - `--array=0-2`（seed 42, 43, 44）、$\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$ の計 18 モデルを `v5/models/fp32_sst_math/` にマージし、安全性 4 ベンチ（`--limit 320 --use_vllm`）＋ Math 2 ベンチ（`gsm8k,minerva_math500`）＋ HarmBench 13B 再分類を `v5/results/fp32_sst_math/` に出力。
- **投入前の事前マスク検証（CPU、全 3 seed × 224 テンソル = 672 テンソル）**:
  - [mask_preflight_verify.json](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp2/mask_preflight_verify.json):
    - `seed42`: `n=224, mean=0.200000, range=[0.200000, 0.200000], inf=0, nan=0`
    - `seed43`: `n=224, mean=0.200000, range=[0.200000, 0.200000], inf=0, nan=0`
    - `seed44`: `n=224, mean=0.200000, range=[0.200000, 0.200000], inf=0, nan=0`
- **SLURM 投入**: `sbatch v5/scripts/slurm_fp32_sst_math.sh` → **Job ID `128590_[0-2]`**（`h100` パーティション）。

## 2. 実証 1：拡張妥当性判定の当て直し前後比較＋人手評価 200 件抽出（完了）
- **スクリプト**: [sok_exp1_reval.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/sok_exp1_reval.py)
- **出力物（`v5/outputs/sok_exp1/`）**:
  - [before_after_summary.md](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp1/before_after_summary.md) / [before_after_summary.json](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp1/before_after_summary.json)（入力 1,872 ファイル、全 156 点）
  - [before_after_vrr_alpha06.png](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp1/before_after_vrr_alpha06.png) / [before_after_vsr_alpha06.png](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp1/before_after_vsr_alpha06.png)
  - 人手アノテーション 200 件（seed=20261124、5 層均衡抽出）:
    - ブラインド評価用 CSV: [human_eval_200_blind.csv](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp1/human_eval_200_blind.csv)
    - 照合用キー JSON: [human_eval_200_key.json](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_exp1/human_eval_200_key.json)（`S1_ext_flagged`: 50、`S2_cross_valid`: 50、`S3_math_valid`: 40、`S4_disagree_valid`: 40、`S5_rule_gib`: 20）
- **主な結果（α=0.6 主結果）**:
  - `safety+math`: VRR・VSR・順位ともに全手法ほぼ変化なし（VRR≥80% 通過 8 → 8）。
  - `safety+code`: VRR≥80% 通過が 5 → 2 手法へ激減（`dare`: 97.9%→2.4%, 順位 2→9、`della`: 92.5%→3.2%, 3→7、`sst`: 87.6%→9.5%, 4→6。一方 `led_merging`: 6→2、`task_arithmetic`: 7→3）。
  - `safety+medical`: `safemerge`（100%→100%）を除く全手法が VRR 0.00% へ急落（通過 4 → 1 手法）。
  - `safety+math+code+medical`: `della`（86.2%→0.0%, 順位 1→6）など激変し、通過 1 → 0 手法（順位 1 位は `task_arithmetic` へ交代）。

## 3. 外部コード監査（`v3/baselines/`）および `ccs.md` 同期（完了）
- [external_code_audit.md](file:///mnt/nas/home/hiromi/src/sst_v2/v5/outputs/sok_audit/external_code_audit.md): SafeMERGE / LED-Merging / MergeAlign / mergekit の P1〜P5 実装事実を行番号付きで整理。
  - SafeMERGE は明示的 `float32`＋層ごとの JSON ログ出力を実装（良好事例）。一方、LED-Merging は `bfloat16`＋`>= threshold` でマージ実効比率ログなし、MergeAlign は公式 `LlamaGuardInference`（`infer.py`）が単一判定器かつ崩壊除外なし（P1・P2 を直接確認）、mergekit は fp16 演算・実効統計なし・`--allow-crimes` 通過。
- [v5/docs/ccs.md](file:///mnt/nas/home/hiromi/src/sst_v2/v5/docs/ccs.md): ユーザー共有の最新版（23 列・P5 列追加・DLSP 書誌更新・v1 確認済み反映）に同期済み。
- NFR2 保全確認: `git status --short -- v3/results v1 v2` が空であることを確認済み。
