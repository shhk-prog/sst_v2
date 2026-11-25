# 修正内容の確認 (Walkthrough): SoK 実証 2 完了監査および最終解析

## 1. 実行健全性・時系列異常の監査結果（異常ゼロ）
- **完了時刻**: 2026-11-25 08:26:18 に全 3 task (`seed 42, 43, 44` + 対照 2 本) が正常終了 (`all done`)。
- **ログ監査**: `03:52` の再開以降、`Traceback` / `Exception` / `Fallback` / `OOM` / `Killed` は **0 件**。`.tmp` 残骸も **0 件**。
- **ファイル完全性**: 安全性 **80 / 80 JSON**（主 72 + 対照 8）・有用性 **20 / 20 JSON**（主 18 + 対照 2）すべて `status=="success"`, `completed==True`。`response` / `classifier_output` / `harmbench_cls_output` 欠落 **0 件**。
- **04:34 GPU 切替（`0,1,2` → `1,2,3`）前後の時系列監査**:
  - 切替をまたいだ `α=0.0 wildjailbreak` の 4 分位（Q1〜Q4）平均文字数は全 3 seed で `[426, 400, 382, 391]`、gibberish は `[5, 5, 7, 4]`、token salad は `[0, 0, 0, 0]` と完全一致。
  - `α=0.0` の Math 正答率は全 3 GPU（GPU 1, 2, 3）で `GSM8K=6.25%, Minerva500=5.94%` と完全一致。
  - 対照 2 本（`controls_seed42`）と元 `v3` 結果の差は TA で安全性 **+0.00 pp**・Math **+0.16 pp**、fp16 SST で安全性 **-0.32〜+0.47 pp**・Math **-0.16 pp** と GPU ドリフトはほぼゼロ。

## 2. 本番解析の出力 (`v5/scripts/analyze_sok_exp2.py`)
- レポート: `v5/outputs/sok_exp2/exp2_analysis_summary.md` / `.json`
- 図: `v5/outputs/sok_exp2/exp2_safety_utility_curve.png`（3 分類器別曲線）, `exp2_injection_ratio_curve.png`（実効安全注入量スケール別）
- 主な知見:
  - P5 修正により実効注入量比（対 TA）が `1.000`（中央値）/ `0.704`（平均）→ **`0.197`** に正常化。
  - 同一名目 α では注入量が約 1/5 になるため曲線が大きくシフトし（例: `α=0.6` で Cond.ASR HB `17.05%` → `32.51%`、`α=0.8` で `15.60%`、`α=1.0` で `7.76%` / StrongREJECT `0.53%`）、固定 α 比較の危うさが実証された。
  - `fp32 SST` の Math は α=0.0〜1.0 全域で `5.94〜6.20%` と WizardMath 基準を維持し、TA `α=1.0` の崩壊（`0.62%`）を起こさなかった。
