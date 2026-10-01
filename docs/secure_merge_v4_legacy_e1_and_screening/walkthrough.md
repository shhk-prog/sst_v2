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

### 2. 正式な手法選択に基づく 3-Seed 主比較表 (Legacy E1 Screening Protocol)

実験計画書に基づき、**「Development (Seed 42) で設定を1つ選択・固定し、その設定を Seed 42, 43, 44 に適用した 3-Seed Mean ± SD」** を算出。
（個別 seed での一番良い結果をチェリーピックするのではなく、正式な評価プロトコルとして集計）

#### 表名: **Top Candidates Satisfying Harmful-Side Constraints by Combined Math Utility**

| Method | Fixed Setting | ASR_all (mean±sd) | ASR_valid (mean±sd) | VRR harmful (mean±sd) | VSR (mean±sd) | GSM8K (mean±sd) | MATH500 (mean±sd) | **$U_{math}$ (mean±sd)** | Harmful-Side Feasible (3/3)? |
|---|---|---|---|---|---|---|---|---|---|
| **`diagonal_sst_main`** | $\alpha=1.0$ | **0.0 ± 0.0%** | **0.0 ± 0.0%** | **100.0 ± 0.0%** | **100.0 ± 0.0%** | 15.7 ± 2.2% | 4.0 ± 1.5% | **9.8 ± 0.4%** | **PASS (3/3)** |
| **`task_arithmetic`** (Linear) | $\alpha=0.8$ | **0.0 ± 0.0%** | **0.0 ± 0.0%** | **100.0 ± 0.0%** | **100.0 ± 0.0%** | 14.7 ± 2.3% | 3.5 ± 0.1% | **9.1 ± 1.2%** | **PASS (3/3)** |
| **`ties`** | $\alpha=0.8$ | 0.6 ± 0.5% | 0.6 ± 0.5% | **100.0 ± 0.0%** | 99.4 ± 0.5% | 9.2 ± 1.1% | 3.8 ± 0.9% | **6.5 ± 0.5%** | **PASS (3/3)** |
| **`dare`** | $\alpha=0.8$ | 3.4 ± 3.4% | 3.4 ± 3.4% | **100.0 ± 0.0%** | 96.6 ± 3.4% | 8.2 ± 0.8% | 4.5 ± 0.8% | **6.4 ± 0.6%** | FAIL/PARTIAL |
| **`matena_fisher`** | default | 6.9 ± 0.5% | 6.1 ± 0.3% | 99.1 ± 0.4% | 93.1 ± 0.5% | 8.0 ± 0.8% | 4.1 ± 0.7% | **6.0 ± 0.7%** | FAIL/PARTIAL |
| **`data_free_sst_main`** | $\alpha=1.0$ | 10.8 ± 6.8% | 10.8 ± 6.8% | **100.0 ± 0.0%** | 89.2 ± 6.8% | 7.2 ± 0.4% | 4.6 ± 0.9% | **5.9 ± 0.6%** | FAIL/PARTIAL |
| **`della`** | $\alpha=0.8$ | 2.8 ± 3.1% | 2.8 ± 3.1% | **100.0 ± 0.0%** | 97.2 ± 3.1% | 8.4 ± 1.6% | 3.1 ± 0.4% | **5.8 ± 0.9%** | FAIL/PARTIAL |
| **`led_merging`** | default | 29.7 ± 0.0% | 11.5 ± 0.0% | 79.1 ± 0.0% | 70.0 ± 0.0% | 0.0 ± 0.0% | 2.8 ± 0.0% | **1.4 ± 0.0%** | FAIL/PARTIAL |
| **`safemerge`** | default | 12.2 ± 17.3% | 9.6 ± 13.6% | 95.6 ± 6.2% | 87.2 ± 18.0% | 0.7 ± 0.6% | 1.9 ± 1.6% | **1.3 ± 0.7%** | FAIL/PARTIAL |
| **`mergealign`** | default | 100.0 ± 0.0% | 100.0 ± 0.0% | 0.0 ± 0.0% | 0.0 ± 0.0% | 0.0 ± 0.0% | 0.0 ± 0.0% | **0.0 ± 0.0%** | FAIL/PARTIAL |

> [!NOTE]
> **重要な分析**:
> 3-Seed 全てで Harmful-side Feasible（$ASR_{valid} \le 5\%, VRR \ge 95\%$）を達成できたのは **Diagonal SST ($\alpha=1.0$), Linear ($\alpha=0.8$), TIES ($\alpha=0.8$)** の3手法のみ。
> DARE/DELLA はシードによる ASR の跳ねがあり、Fisher/Data-Free SST は安全基準未達、LED は Degeneration 崩壊、SafeMerge は Utility 喪失となりました。

---

### 3. Linear Candidate-Level Canonical Equivalence の実測検証

`v4/scripts/audit/verify_linear_candidate_equivalence.py` により、
`canonicalize(v3 Linear α=.6 checkpoint)` vs `v4 新マージ Linear α=.6` を直接比較：

1. **Parameter Exact Match**:
   - 291/291 全テンソルキーが完全一致。
   - 平均絶対誤差: **$9.13 \times 10^{-6}$**（fp16 演算の丸め誤差水準）。
2. **Tokenizer Match**:
   - 複数プロンプトでの Tokenizer Input IDs が **完全一致 (PASS)**。
3. **Greedy Generation Match**:
   - 有害プロンプトおよび数学プロンプトに対する Greedy Generation 出力トークン列が **100% 完全一致 (PASS: IDENTICAL)**。

これにより、**Linear に関しては「v3 response = canonical Production E1 response」として数学的・実測的に正式再利用（FULL_REUSE）できることが証明されました。**

---

## 4. 今後の具体的実行順（フェーズ移行計画）

- **Phase 1: Human Validity 200件のアノテーション・評価**
  - ランダム150件＋難例50件の評価（Cohen's $\kappa$, Precision, Recall, F1）
- **Phase 2: XSTest 8モデルの Benign VRR & Over-refusal 評価**
  - 対象: Base, WizardMath, SafetyFT, Linear (.6, .8), Diagonal SST (.8, 1.0), TIES (.8)
  - `HARMFUL_SIDE_FEASIBLE` から正式な `FULL_FEASIBLE / INFEASIBLE` への昇格判定
- **Phase 3: Legacy E1 Final Table の確定**
  - 3-Seed 集計結果、過剰拒否、人手妥当性を集約した Legacy-screening 最終表
- **Phase 4: Canonical Production E1**
  - Linear は再利用、Diagonal SST (.8, 1.0) と TIES (.8) のみ canonical source から再マージ・再生成
- **Phase 5: E2 重み空間の機序解析**
  - 成功モデル（Linear .8, Diagonal SST best） vs 失敗類型（Safety Failure, Degeneration Failure, Utility Failure）の重み幾何解析
- **Phase 6: E3 統制介入実験**
