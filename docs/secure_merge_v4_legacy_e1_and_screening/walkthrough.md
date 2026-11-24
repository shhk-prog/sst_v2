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

### 2. 評価データセット役割分担に基づく全10手法の総合結果表 (3-Seed Protocol: Mean ± SD)

各ベンチマークの役割を明確に分離した評価結果：
- **Safety 4大ベンチマーク (Harmful)**: HarmBench, JailbreakBench, StrongReject, WildJailbreak（同一Judgeによる $ASR_{valid}$）
- **Math Primary Utility ($U_{math}$)**: GSM8K, MATH-500 ($U_{math} = (\text{GSM8K} + \text{MATH500}) / 2$)
- **General Utility Guardrails (Secondary)**: IFEval, MMLU（能力崩壊の検知、単一平均せず個別報告。未測定は N/A と表記）

#### 表名: **Comprehensive Multi-Benchmark Results across 10 Merge Methods (Fixed Setting, 3-Seed Mean ± SD)**

| # | 手法 (Method) | 設定 (Setting) | HarmBench | JailbreakB | StrongRej | WildJailB | VRR-H | GSM8K | MATH500 | **$U_{math}$ (Primary)** | IFEval | MMLU | Gate 1 判定・Legacy位置づけ |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | **SST-Merge (Diagonal)** | $\alpha=1.0$ | **0.0±0.0%** | **0.0±0.0%** | **0.0±0.0%** | **0.0±0.0%** | **100.0±0.0%** | 15.7±2.2% | 4.0±1.5% | **9.8±0.4%** | 13.4±0.0% | 26.5±0.0% | **HARMFUL_FEASIBLE (Screening Leader)** |
| 2 | **Linear Safety-Patch** | $\alpha=0.8$ | **0.0±0.0%** | **0.0±0.0%** | **0.0±0.0%** | **0.0±0.0%** | **100.0±0.0%** | 14.7±2.3% | 3.5±0.1% | **9.1±1.2%** | 14.4±0.0% | 27.9±0.0% | **HARMFUL_FEASIBLE (Reference Baseline)** |
| 3 | **TIES** | $\alpha=0.8$ | 0.4±0.6% | **0.0±0.0%** | 1.1±1.1% | 0.6±0.5% | **100.0±0.0%** | 9.2±1.1% | 3.8±0.9% | **6.5±0.5%** | N/A | N/A | **HARMFUL_FEASIBLE (干渉抑制Baseline)** |
| 4 | **DARE** | $\alpha=0.8$ | 3.8±4.9% | 4.7±6.6% | 4.5±3.7% | 1.5±1.1% | **100.0±0.0%** | 8.2±0.8% | 4.5±0.8% | **6.4±0.6%** | N/A | N/A | FAIL (安全基準境界・シード不安定) |
| 5 | **Fisher-weighted** | default | 6.9±1.1% | 6.3±1.2% | 4.9±0.6% | 6.5±1.5% | 99.1±0.4% | 8.0±0.8% | 4.1±0.7% | **6.0±0.7%** | N/A | N/A | FAIL (全安全ベンチマークでASR>5% 防御未達) |
| 6 | **Data-Free SST** | $\alpha=1.0$ | 9.8±6.1% | 15.0±11.5% | 10.5±6.5% | 10.6±7.1% | **100.0±0.0%** | 7.2±0.4% | 4.6±0.9% | **5.9±0.6%** | 11.9±0.0% | 27.5±0.0% | FAIL (Data-Freeの限界: ASR高) |
| 7 | **DELLA** | $\alpha=0.8$ | 3.8±4.9% | 2.0±2.8% | 3.7±3.4% | 1.2±1.2% | **100.0±0.0%** | 8.4±1.6% | 3.1±0.4% | **5.8±0.9%** | N/A | N/A | FAIL (安全基準境界・シード不安定) |
| 8 | **LED-Merging** | default | 6.2±0.0% | 11.0±0.0% | 10.7±0.0% | 19.1±0.0% | 79.1±0.0% | 0.0±0.0% | 2.8±0.0% | **1.4±0.0%** | N/A | N/A | FAIL (Degeneration 崩壊: VRR 79%) |
| 9 | **SafeMERGE** | default | 7.4±10.5% | 13.6±19.2% | 10.8±15.3% | 9.4±13.3% | 95.6±6.2% | 0.7±0.6% | 1.9±1.6% | **1.3±0.7%** | N/A | N/A | FAIL (ASR未達 & Utility喪失) |
| 10| **MergeAlign** | default | N/A | N/A | N/A | N/A | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% | **0.0±0.0%** | N/A | N/A | FAIL (完全生成崩壊: valid 0件) |

> [!IMPORTANT]
> **General Guardrail の「N/A」に関する監査結果**:
> 実測監査により、TIES, DARE, DELLA, Fisher, LED, SafeMERGE, MergeAlign は Math マージモデルにおいて IFEval / MMLU が元々測定されておらず、欠損値（missing utility）であったことが判明しました。
> したがって、これらを「能力崩壊（0.0%）」とみなすのは誤りであり、現段階では **partial General Guardrail** として扱い、未測定項目は `N/A` と明記します。

---

### 3. 現段階での候補の位置づけ（3大群・8分類）

現段階の結論は「SSTがBest」と確定するのではなく、**「Legacy screeningにおけるHarmful-side constraints通過候補の中では、Diagonal SST $\alpha=1.0$ が最も高い $U_{math}$ を示した（Leading Candidate）」** です。
Gate 2（XSTest: Benign VRR $\ge 95\%$, Over-refusal $\le 10\%$）が完了するまで、正式な `FULL_FEASIBLE` および最終勝者は確定しません。

| 群 | 手法 | 現在の位置づけ |
|---|---|---|
| **Group A: Harmful-Side Successful** | **SST-Merge (Diagonal)** | Legacy screeningの最有力候補 (Screening Leader) |
| | **Linear Safety-Patch** | 最有力reference / simple baseline (FULL_REUSE確認済み) |
| | **TIES** | Harmful-sideを通った重要baseline |
| **Group B: Safety-Limited** | **DARE / DELLA** | seed-sensitive safety failure |
| | **Fisher-weighted** | safety threshold failure (全シードでASR>5%) |
| | **Data-Free SST** | data-free selectiveの安全性不足候補 |
| **Group C: Severe Functionality Failure** | **LED-Merging** | degeneration failure代表 (VRR 79.1%) |
| | **SafeMERGE** | safety/utility failure代表 ($U_{math} \sim 1.3\%$) |
| | **MergeAlign** | complete degeneration代表 (VRR 0%, ASR 0%) |

この分類は、そのまま **E2（重み空間の機序解析）における「成功 vs 失敗原因別」の比較候補** として活用されます。

---

### 4. 次の具体的実行順（GPU側の修正反映）

- **Human 側**:
  - 準備済みの [`blinded_human_audit_sheet.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/human_audit/blinded_human_audit_sheet.json)（200件）に対し、二重盲検アノテーション $\to$ 合議 $\to$ [`evaluate_human_audit.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/audit/evaluate_human_audit.py) で Precision, Recall, F1, Cohen's $\kappa$ を算出。
- **GPU 側**:
  1. **非Linear 9手法の Canonical Production 再マージ**:
     - 代表固定設定（各3 seed、計27候補）を canonical source（32,000共通空間）から新マージ・保存 $\to$ E0 sanity check。
  2. **30 Production Candidates の確定**:
     - Linear Safety-Patch (3候補: FULL_REUSE) ＋ 非Linear (27候補) ＝ 計30候補。
  3. **XSTest の実行**:
     - 上記 30 候補 ＋ 3 基準モデル（Base, WizardMath, SafetyFT）の計 33 モデルに対し、XSTest 200 問を実行。
  4. **Gate 2 判定（FULL_FEASIBLE 昇格）と 不足ベンチマークの補完生成**:
     - XSTest による過剰拒否判定を行い、正式な `FULL_FEASIBLE` および最終 Best Method を決定。
