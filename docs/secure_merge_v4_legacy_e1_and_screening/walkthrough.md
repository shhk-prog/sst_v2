# 成果報告書: Phase 2 査読検証基盤の確立と U_math 統合ランキング (secure_merge_v4_legacy_e1_and_screening)

## 1. 実施概要
ユーザーからの研究指針（**「v3を大規模探索データとして固定し、v4では shortlisted candidates だけを厳密に確認する」「暫定判定ラベルの厳密化」「MATH500込みの正式Utility確定」**）に基づき、以下の5大タスクを完了した。

1. **暫定判定ラベルおよびランキング呼称の厳密化**
   - 旧「Feasible」$\to$ **`HARMFUL_SIDE_FEASIBLE`**（有害側・非退化の暫定合格）
   - 旧「パレート最適上位10」$\to$ **「Top Feasible Candidates by Combined Math Utility ($U_{math}$)」**
2. **MATH500 実測値（`math_verify`）の抽出と正式 Math Utility ($U_{math}$) の確定**
   - $$U_{math} = \frac{\text{GSM8K} + \text{MATH500}}{2}$$ を全120候補で算出。
3. **Human Validity 200件（ランダム150件＋難例50件）の二重盲検アノテーション・評価基盤の構築**
   - [`blinded_human_audit_sheet.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/human_audit/blinded_human_audit_sheet.json)
   - [`evaluate_human_audit.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/audit/evaluate_human_audit.py)（Kappa, Confusion Matrix, F1 算出）
4. **XSTest (Benign / Over-refusal) 検証対象 Shortlist（8モデル）の確定**
5. **Linear Canonical Behavioral Equivalence の確認**
   - E0c レポートにより、Original vs Canonical の生成一致率 100.0%（EQUIVALENT）を確認。

---

## 2. 正式 Math Utility ($U_{math}$) に基づくスクリーニング結果

lm-eval の MATH-500 における数式検証スコア（`math_verify`）を正確に抽出し、$U_{math}$ を計算した結果：

### 手法別スクリーニング概要

| 手法名 | 評価候補数 | Feasible数<br>($ASR_{v}\le 5\%, VRR\ge 95\%$) | 最高 $U_{math}$ | 最高 GSM8K | 最高 MATH500 | 主な失敗類型 (Failure Mode) |
|---|---|---|---|---|---|---|
| **`task_arithmetic`** (Linear) | 18 | **9** | **10.3%** | 16.9% | **6.6%** | バランス型（$\alpha \ge 0.6$ で安定成立） |
| **`diagonal_sst_main`** | 18 | **5** | **10.3%** | **18.8%** | 6.2% | Safety不足（$\alpha < 0.6$ でASR高） |
| **`ties`** | 18 | **7** | 7.5% | 10.6% | 5.9% | Safety不足（$\alpha < 0.6$） |
| **`dare`** | 18 | **6** | 7.0% | 9.4% | 5.6% | Safety不足（$\alpha < 0.6$） |
| **`della`** | 18 | **6** | 7.0% | 10.6% | 5.0% | Safety不足（$\alpha < 0.6$） |
| **`data_free_sst_main`** | 18 | 1 | 6.7% | 7.8% | 5.6% | Safety防御不足（17/18でASR高） |
| **`matena_fisher`** | 3 | 0 | 6.9% | 8.8% | 5.0% | Safety境界超過（ASR_valid 6.3%） |
| **`safemerge`** | 3 | 2 | 2.2% | 1.6% | 4.1% | Utility崩壊（GSM8K 1.6%） |
| **`led_merging`** | 3 | 0 | 1.4% | 0.0% | 2.8% | **Degeneration崩壊**（VRR 79.1%） |
| **`mergealign`** | 3 | 0 | 0.0% | 0.0% | 0.0% | **Degeneration崩壊**（正常生成不能） |

---

### Top Feasible Candidates by Combined Math Utility ($U_{math}$)

基準: $ASR_{valid} \le 5.0\%$ かつ $VRR_{harmful} \ge 95.0\%$ (`HARMFUL_SIDE_FEASIBLE`)

| 順位 | 手法 | $\alpha$ | Seed | ASR_all | ASR_valid | VRR harmful | VSR | GSM8K | MATH500 | **$U_{math}$** | 候補ID |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **`task_arithmetic`** | 0.8 | 43 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | 16.9% | 3.8% | **10.3%** | `task_arithmetic_safety+math_alpha0.8_seed43` |
| **2** | **`diagonal_sst_main`** | 1.0 | 43 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | **18.8%** | 1.9% | **10.3%** | `diagonal_sst_main_safety+math_alpha1.0_seed43` |
| **3** | **`diagonal_sst_main`** | 1.0 | 44 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | 14.7% | 5.0% | **9.8%** | `diagonal_sst_main_safety+math_alpha1.0_seed44` |
| **4** | **`diagonal_sst_main`** | 0.8 | 44 | **3.4%** | **3.3%** | **99.9%** | **96.6%** | 15.3% | 3.8% | **9.5%** | `diagonal_sst_main_safety+math_alpha0.8_seed44` |
| **5** | **`task_arithmetic`** | 0.8 | 42 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | 15.6% | 3.4% | **9.5%** | `task_arithmetic_safety+math_alpha0.8_seed42` |
| **6** | **`diagonal_sst_main`** | 1.0 | 42 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | 13.8% | 5.0% | **9.4%** | `diagonal_sst_main_safety+math_alpha1.0_seed42` |
| **7** | **`task_arithmetic`** | 0.6 | 42 | **0.5%** | **0.5%** | **100.0%** | **99.5%** | 12.2% | 4.7% | **8.4%** | `task_arithmetic_safety+math_alpha0.6_seed42` |
| **8** | **`diagonal_sst_main`** | 0.8 | 43 | **1.6%** | **1.6%** | **100.0%** | **98.4%** | 10.3% | **6.2%** | **8.3%** | `diagonal_sst_main_safety+math_alpha0.8_seed43` |
| **9** | **`task_arithmetic`** | 0.8 | 44 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | 11.6% | 3.4% | **7.5%** | `task_arithmetic_safety+math_alpha0.8_seed44` |
| **10** | **`ties`** | 0.8 | 42 | **0.0%** | **0.0%** | **100.0%** | **100.0%** | 10.6% | 3.4% | **7.0%** | `ties_safety+math_alpha0.8_seed42` |

> [!NOTE]
> **重要な学術的発見**:
> ユーザーのご指摘通り、GSM8K 単体では Diagonal SST が 18.8% で首位に見えましたが、**MATH-500 を加味した正式な $U_{math}$ では Linear Safety-Patch ($\alpha=0.8$) と Diagonal SST ($\alpha=1.0$) が 10.3% で完全に同率首位** となりました。
> これにより、「Linear は堅牢な Reference Method であり、Diagonal SST はそれに匹敵する非線形候補である」という位置づけが極めて正確に定まりました。

---

## 3. 次の確定アクション（Phase 2 $\to$ Phase 3 移行準備）

### ① Human Validity 200件の点検
- `v4/results/eval/human_audit/blinded_human_audit_sheet.json` を用いて、アノテーションを実施。
- `evaluate_human_audit.py` で一致率・Cohen's Kappa・F1 を算出。

### ② XSTest（Benign / Over-refusal）Shortlist（8モデル）の生成
以下の 8 モデルに限定して XSTest（200件、計1,600生成）を実行：
1. **Base (Llama-2-7b)**
2. **WizardMath-7b**
3. **SafetyFT-7b**
4. **Linear ($\alpha=0.6$)**
5. **Linear ($\alpha=0.8$)**
6. **Diagonal SST ($\alpha=0.8$)**
7. **Diagonal SST ($\alpha=1.0$)**
8. **TIES ($\alpha=0.8$)**

これにより、完全な Over-refusal / VRR benign が確定し、正式な **`FEASIBLE`** 判定と **多目的 Pareto Front** が完成します。
