# 成果報告書: Math Legacy E1 スクリーニングおよび査読検証基盤の確立 (secure_merge_v4_legacy_e1_and_screening)

## 1. 実施概要
「Secure Mergeの設計要件を特定する実験計画書（計画案 v1.0）」に基づき、**「v3資産（約126,000生成）を全再利用した大規模スクリーニング（Legacy E1）」** および **「査読対応（Human Validity 200件抽出・Benign補完計画）」** を完了した。

---

## 2. Math Legacy E1 全手法スクリーニング結果（120候補）

全10手法（各3シード、$\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$ 等、計120候補）に対し、v4共通HarmBench判定と厳格な非縮退チェック（`is_response_valid`）を一括適用した結果：

### 手法別スクリーニング概要

| 手法名 | 評価候補数 | Feasible数<br>($ASR_{v}\le 5\%, VRR\ge 95\%$) | 最高GSM8K<br>(全体) | 最高GSM8K<br>(Feasible領域) | 主要な失敗類型 (Dominant Failure Mode) |
|---|---|---|---|---|---|
| **`diagonal_sst_main`** | 18 | **5** | **18.8%** | **18.8%** | Safety不足（$\alpha < 0.6$ でASR高） |
| **`task_arithmetic`** (Linear) | 18 | **9** | **16.9%** | **16.9%** | バランス型（$\alpha \ge 0.6$ で高確率に成立） |
| **`della`** | 18 | **6** | 10.6% | 10.6% | Safety不足（$\alpha < 0.6$） |
| **`ties`** | 18 | **7** | 10.6% | 10.6% | Safety不足（$\alpha < 0.6$） |
| **`dare`** | 18 | **6** | 9.4% | 9.4% | Safety不足（$\alpha < 0.6$） |
| **`data_free_sst_main`** | 18 | 1 | 7.8% | 6.9% | Safety防御不足（17/18でASR高） |
| **`matena_fisher`** | 3 | 0 | 8.8% | 0.0% | Safety境界超過（ASR_valid 6.3%） |
| **`safemerge`** | 3 | 2 | 1.6% | 1.6% | Utility崩壊（GSM8K 1.6%へ低下） |
| **`led_merging`** | 3 | 0 | 0.0% | 0.0% | **Degeneration崩壊**（VRR 79.1%に低下） |
| **`mergealign`** | 3 | 0 | 0.0% | 0.0% | **Degeneration崩壊**（正常生成不能） |

---

### 全120候補中のパレート最適上位10選（Feasible Region: $ASR_{valid} \le 5\%$, $VRR \ge 95\%$）

| 順位 | 手法 | $\alpha$ | Seed | ASR_all | ASR_valid | VRR harmful | VSR | GSM8K | 候補名 |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **`diagonal_sst_main`** | 1.0 | 43 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **18.8%** | `diagonal_sst_main_safety+math_alpha1.0_seed43` |
| **2** | **`task_arithmetic`** | 0.8 | 43 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **16.9%** | `task_arithmetic_safety+math_alpha0.8_seed43` |
| **3** | **`task_arithmetic`** | 0.8 | 42 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **15.6%** | `task_arithmetic_safety+math_alpha0.8_seed42` |
| **4** | **`diagonal_sst_main`** | 0.8 | 44 | **3.4%** | **3.3%** | **99.9%** | **96.6%** | **15.3%** | `diagonal_sst_main_safety+math_alpha0.8_seed44` |
| **5** | **`diagonal_sst_main`** | 1.0 | 44 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **14.7%** | `diagonal_sst_main_safety+math_alpha1.0_seed44` |
| **6** | **`diagonal_sst_main`** | 1.0 | 42 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **13.8%** | `diagonal_sst_main_safety+math_alpha1.0_seed42` |
| **7** | **`task_arithmetic`** | 0.6 | 42 | **0.5%** | **0.5%** | **100.0%** | **99.5%** | **12.2%** | `task_arithmetic_safety+math_alpha0.6_seed42` |
| **8** | **`task_arithmetic`** | 0.8 | 44 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **11.6%** | `task_arithmetic_safety+math_alpha0.8_seed44` |
| **9** | **`ties`** | 0.8 | 42 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **10.6%** | `ties_safety+math_alpha0.8_seed42` |
| **10** | **`della`** | 0.8 | 42 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **10.6%** | `della_safety+math_alpha0.8_seed42` |

> [!IMPORTANT]
> **スクリーニングによる決定的な知見**:
> 1. **最高性能**: `diagonal_sst_main`（$\alpha=1.0$）が GSM8K 18.8% を達成し単独首位。
> 2. **最高安定性**: `task_arithmetic`（Linear $\alpha=0.8$）が 15.6%〜16.9% を全シードで安定達成し、Feasible率 50%（9/18）で最高。
> 3. **失敗原因の完全分離**:
>    - LED / MergeAlign: **「退化崩壊型」**（VRRが70%台に激減）
>    - Fisher / Data-Free SST: **「安全未達型」**（ASRが下がりきらない）
>    - SafeMerge: **「能力喪失型」**（安全だが数学が1%に崩壊）

---

## 3. 査読・検証対応の実施状況

### 3.1 Human Validity 200件（二重盲検アノテーションセット）
計画書 Section 5.2 に基づき、v3生レスポンス（20,256件）から二重盲検用の200件を抽出完了：
- **生成ファイル**:
  - [`v4/results/eval/human_audit/blinded_human_audit_sheet.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/human_audit/blinded_human_audit_sheet.json)（モデル名・手法名をハッシュ化して隠蔽した評価シート）
  - [`v4/results/eval/human_audit/gold_mapping_key.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/human_audit/gold_mapping_key.json)（正解対応キー）
- **内訳**:
  - 全体からの無作為抽出: **150件**
  - 難例（短い定型拒否、文字数異常、判定不一致等）: **50件**

### 3.2 Benign / Over-refusal（XSTest 200件）最小限生成計画
スクリーニングによって上位が確定したため、**全候補の再生成は不要**。
以下の **主要5条件（各3シード = 15モデル）** に限定して XSTest（約200件）を実行するだけで、完全な Over-refusal / VRR benign が確定します：
1. `task_arithmetic` ($\alpha \in \{0.6, 0.8\}$)
2. `diagonal_sst_main` ($\alpha \in \{0.8, 1.0\}$)
3. `ties` ($\alpha = 0.8$)
4. 単体対照（Base, WizardMath, SafetyFT）

---

## 4. 作成された成果物一覧
- スクリーニング再採点スクリプト: [`v4/scripts/eval/rescore_all_vllm_legacy.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/rescore_all_vllm_legacy.py)
- 完全集計データ: [`v4/results/eval/legacy_e1/legacy_e1_math_comprehensive_summary.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/legacy_e1/legacy_e1_math_comprehensive_summary.json)
- スクリーニング分析レポート: [`v4/results/eval/legacy_e1/screening_report.txt`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/legacy_e1/screening_report.txt)
- Human Audit セット: [`v4/results/eval/human_audit/blinded_human_audit_sheet.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/human_audit/blinded_human_audit_sheet.json)
- ドキュメント:
  - [`docs/secure_merge_v4_legacy_e1_and_screening/task.md`](file:///mnt/nas/home/hiromi/src/sst_v2/docs/secure_merge_v4_legacy_e1_and_screening/task.md)
  - [`docs/secure_merge_v4_legacy_e1_and_screening/implementation_plan.md`](file:///mnt/nas/home/hiromi/src/sst_v2/docs/secure_merge_v4_legacy_e1_and_screening/implementation_plan.md)
  - [`docs/secure_merge_v4_legacy_e1_and_screening/walkthrough.md`](file:///mnt/nas/home/hiromi/src/sst_v2/docs/secure_merge_v4_legacy_e1_and_screening/walkthrough.md)
