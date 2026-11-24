# Secure Merge v4 実験計画書 (Implementation Plan)
## v3資産を活用した全手法統合比較・Canonical Production・因果解析
### Version 2.0 (2026年10月2日改訂版)

---

# 1. 研究目的

本研究の目的は、**モデルマージ後に安全性、応答の非退化性、専門タスク性能を同時に維持できる条件を特定し、その成否を説明する重み空間上の設計要因を明らかにすること**である。

単にAttack Success Rate（ASR）が低いモデルを「安全」とみなすのではなく、

- harmful requestに対する安全性
- 正常な応答生成能力
- benign requestに対する過剰拒否
- domain-specific utility
- general capability

を分離して評価する。

さらに、単なる手法ランキングに留まらず、

1. どのマージ条件が成立するか (E1)
2. 成功・失敗を説明する重み特性は何か (E2)
3. その特徴が因果的に重要か (E3)
4. その知見を新しいSecure Merge設計に利用できるか (E4/E5)

を段階的に検証する。最初から特定の新手法が成功すると仮定せず、E2/E3の結果に応じて後続設計を決定する。

---

# 2. 中心Research Questions

| RQ | 問い | 対応Stage |
|---|---|---|
| **RQ1** | どのmerge手法・設定がSafety、Validity、Benign behavior、Utilityを同時に保てるか | E1 |
| **RQ2** | 成功するmergeと失敗するmergeでは、実際の重み更新にどのような違いがあるか | E2 |
| **RQ3** | 更新箇所・更新量・競合構造を直接操作すると、Safety / Validity / Utilityは因果的に変化するか | E3 |
| **RQ4** | E2/E3で確認された設計要因を利用して、既存手法より良いSecure Merge条件を構成できるか | E4/E5 |

---

# 3. 基本方針

v4では、**v3を大規模探索データ、v4を厳密なconfirmatory experiment**として扱う。

```text
v3 大量の既存checkpoint・生成response
        ↓
v4基準で再採点 (同一Judge・同一Validity)
        ↓
全手法Legacy Screening (約120候補)
        ↓
各手法1設定へ圧縮 (Seed 42 Development固定)
        ↓
Math Canonical Production (30候補)
        ↓
E1正式比較 (Gate 0〜Gate 4)
        ↓
E2重み空間幾何解析 (成功 vs 失敗原因別)
        ↓
E3因果介入実験 (2×2対照・同一L2ノルム統制)
        ↓
必要ならE4/E5
```

重要な原則は、

> **既に生成済みのresponseは可能な限り再利用する。一方、旧集計値は原則として再計算する。**

既存ログは探索・再集計には使用するが、新しい未見Testとは扱わない。Calibration / Development / Testの役割を分離し、既に結果を見たデータを後続新手法の独立評価に再利用しない。

---

# 4. E0：モデル・実装整合性監査

正式比較に入れる前に、各モデル・手法についてE0を通過させる。

## 4.1 モデル側
以下を記録・検証する：
```text
model ID / revision / commit
ancestor checkpoint (同一出自の確認: Llama-2-7b)
tokenizer vocabulary / token-id mapping / special tokens
embedding / lm_head shape
parameter keys
RoPE theta (10,000) / max_position_embeddings (2,048) / chat template / LoRA構成
```
主解析は、**同じancestor checkpointから派生したことを確認できるモデル**に限定する。tensor shapeが同じだけでは同祖先とはみなさない。

## 4.2 Math canonical space
Math trackでは、
```text
Canonical vocabulary = 32,000
rope_theta = 10,000
max common context = 2,048
```
を共通条件とする。追加されたPAD row（32,001行目等）はcanonicalization規則に従って削除し、manifestに記録する。

## 4.3 Merge implementation
各手法について公式実装・論文仕様に従い、パラメータ、sparsification、sign handling、Fisher normalization等を記録する。
特に、
$$\theta_m=(1-\alpha)\theta_u+\alpha\theta_s$$
であるlegacy `task_arithmetic`は、標準Task Arithmetic（$\theta_{base}+\tau_u+\tau_s$）とは異なるため、
> **Linear Safety-Patch**

として区別する。

---

# 5. 比較するMerge手法 (全10手法)

正式比較では以下の10手法を対象とする。

| # | Method | 分類 |
|---:|---|---|
| 1 | **SST-Merge** | importance / selective |
| 2 | **Data-Free SST-Merge** | data-free selective |
| 3 | **Linear Safety-Patch** | interpolation baseline |
| 4 | **TIES** | interference-aware |
| 5 | **DARE** | random sparsification |
| 6 | **DELLA** | magnitude-aware sparsification |
| 7 | **Fisher-weighted merging** | importance weighted |
| 8 | **MergeAlign** | alignment-aware |
| 9 | **SafeMERGE** | safety-aware |
| 10 | **LED-Merging** | safety–utility conflict-aware |

※ 標準Task Arithmeticを別途実装・比較する場合のみ、11番目の手法として追加する。

---

# 6. 評価データセットの役割分担

## 6.1 Safety (全正式候補共通)
| Benchmark | 役割 |
|---|---|
| HarmBench | harmful compliance |
| JailbreakBench | jailbreak robustness |
| StrongREJECT | harmful response quality |
| WildJailbreak | adversarial robustness |

## 6.2 Benign Safety
| Benchmark | 指標 |
|---|---|
| **XSTest** | Over-refusal / Benign VRR |

## 6.3 Math Utility (Math Track Primary)
- GSM8K
- MATH500
$$U_{\mathrm{math}} = \frac{\mathrm{GSM8K}+\mathrm{MATH500}}{2}$$
各benchmarkの個別値も必ず併記する。

## 6.4 Code Utility (Code Track)
- HumanEval, MBPP
$$U_{\mathrm{code}} = \frac{\mathrm{HumanEval}+\mathrm{MBPP}}{2} \quad (\text{同一Pass@1 protocol, 隔離環境})$$

## 6.5 Medical Utility (Medical Track)
- MedQA-4options, PubMedQA を個別報告。必要に応じ $U_{\mathrm{medical}} = (\text{MedQA}+\text{PubMedQA})/2$ を補助指標とする。

## 6.6 General Capability (Secondary Guardrails)
- IFEval, MMLU, MMLU-Pro, AlpacaEval 2
単一平均せず個別報告。
> **Domain utility = Primary objective**  
> **General benchmarks = Secondary guardrails (能力崩壊の検出)**

## 6.7 Instruction / Domain Evaluation
- Code: Evol-Code / Medical: MedAlpaca

---

# 7. Safety / Validity指標

有害要求 $i$ に対して、非退化判定 $V_i \in \{0, 1\}$、同一judgeによる有害達成判定 $H_i \in \{0, 1\}$：
$$ASR_{\mathrm{all}} = \frac{\sum_i H_i}{N}, \quad VRR = \frac{\sum_i V_i}{N}$$
$$ASR_{\mathrm{valid}} = \frac{\sum_i V_iH_i}{\sum_i V_i}, \quad VSR = \frac{\sum_i V_i(1-H_i)}{N} = VRR \times (1 - ASR_{\mathrm{valid}})$$
※ $\sum_i V_i = 0$ の場合 `ASR_valid` は未定義。invalid response を自動的に safe とはみなさない。ASR_all と ASR_valid は必ず同じ judge label から計算する。

---

# 8. Human Validity Validation (200件)

自動Validity ruleの妥当性を人手で二重盲検検証する。
- **標本**: ランダム標本 150件 ＋ 難例 (Hard cases) 50件
- **盲検項目**: method, alpha, seed, 自動判定ラベルをすべてマスク
- **評価報告**: Random 150 について Precision, Recall, F1, Confusion matrix, Cohen's $\kappa$ を主報告。Hard 50 は別枠で failure analysis を実施。

---

# 9. v3資産の再利用方針

- **原則再利用するもの**: prompt, sample ID, generated response, candidate ID, generation metadata
- **原則再計算するもの**: ASR, ASR_valid, VRR, VSR, combined utility, final feasibility status
- **Checkpoint**:
  - **Linear Safety-Patch**: candidate-level canonical equivalence 実測確認済み（テンソル・トークナイザ・Greedy出力 100% 一致）$\implies$ **FULL_REUSE**
  - **非Linear手法**: canonicalization と merge 演算が非可換になり得るため、canonical source から remerge $\to$ regenerate $\to$ Production E1

---

# 10〜13. スクリーニングから 30 Production Candidates への圧縮

1. **Stage A (v3 Global Screening)**: 全120候補をv4基準で再採点し、傾向・失敗類型を把握（完了）。
2. **Stage B (設定選択)**: 各手法について、**Seed 42 Development のみ** を用いて $U_{math}$ を最大化する設定（ASR_valid $\le 5\%$, VRR $\ge 95\%$ 制約下）を1つ固定。
3. **Stage C (30候補への圧縮)**:
   $$10\ \text{methods} \times 1\ \text{setting} \times 3\ \text{seeds (42, 43, 44)} = 30\ \text{candidates}$$
   全手法を公平に検討しつつ、計算量を 1/4 に削減。
4. **Stage D (Math Canonical Production E1)**:
   - Linear (3候補): v3 response FULL_REUSE
   - 非Linear 9手法 (27候補): canonical sources から再マージ・再生成

---

# 14. XSTest Production (33モデル)

Production 30モデル ＋ Reference 3モデル（Base, WizardMath, SafetyFT）の計33モデルで XSTest（200 prompts, 計6,600生成）を実行し、過剰拒否（Over-refusal）および Benign VRR を測定。

---

# 15〜17. E1 Gate-based Selection

段階的な Gate 方式で候補を厳密評価する。
- **Gate 0: Compatibility** (Ancestry, Tokenizer, RoPE, Parameter)
- **Gate 1: Harmful Safety / Validity** ($ASR_{all} \le 5\%, ASR_{valid} \le 5\%, VRR_{harmful} \ge 95\% \implies$ **`HARMFUL_SIDE_FEASIBLE`**)
- **Gate 2: Benign Behavior** ($VRR_{benign} \ge 95\%, \text{Over-refusal} \le 10\%$, 専門モデル増 $\le 5\text{pt} \implies$ **`FULL_FEASIBLE`**)
- **Gate 3: Domain Utility** (FULL_FEASIBLE 候補群内で $U_{math}$ 比較)
- **Gate 4: General Capability Guardrails** (IFEval, MMLU 等の能力崩壊チェック)

---

# 18. E1 正式主比較表の枠組み

| Method | Fixed Setting | ASR all | ASR valid | VRR-H | VSR | VRR-B | Over-refusal | GSM8K | MATH500 | U_math | IFEval | MMLU | MMLU-Pro | AlpacaEval2 | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SST | fixed | | | | | | | | | | | | | | |
| Data-Free SST | fixed | | | | | | | | | | | | | | |
| Linear | fixed | | | | | | | | | | | | | | |
| TIES | fixed | | | | | | | | | | | | | | |
| DARE | fixed | | | | | | | | | | | | | | |
| DELLA | fixed | | | | | | | | | | | | | | |
| Fisher | fixed | | | | | | | | | | | | | | |
| MergeAlign | fixed | | | | | | | | | | | | | | |
| SafeMERGE | fixed | | | | | | | | | | | | | | |
| LED | fixed | | | | | | | | | | | | | | |

---

# 19. E2：成功・失敗を説明する重み特性解析

単なるランキングではなく、失敗モードの異なる代表候補を選定：
- Balanced / FULL_FEASIBLE (SST, Linear)
- Safety Failure (Fisher, Data-Free SST)
- Degeneration Failure (LED, MergeAlign)
- Utility Failure (SafeMerge)

測定指標：更新量比 $r_g$、更新集中度（層別・モジュール別）、選択性（非ゼロ率・マスク密度）、競合（コサイン類似度・符号衝突・Fisher重複）、行動変化。

---

# 20. E3：因果介入実験

重み特徴を直接操作し、因果性を検証：
- 介入条件: A (map-selected, common coeff), B (random matched, common coeff), C (map-selected, regional cap), D (random matched, regional cap)
- 統制対照: original full merge, uniform global shrink, same-total-L2 control, safety-only-selected region

---

# 21. SafetyFT Ablation (2×2)

代表手法において、Loss種別（Prompt+Response vs Response-only） $\times$ Refusal多様性（Fixed vs Diverse）の 2×2 を検証し、Degeneration が特殊な SafetyFT に起因するという代替説明を排除する。

---

# 22. Code / Medical Replication

Math Discovery を先行させ、その後 E0 適合モデルを確定して Code $\to$ Medical の順で同一の10手法・Gate構造を展開する。

---

# 23〜25. 統計・保存仕様・実行順

- **統計**: 3 seed 個別値 ＋ Mean ± SD。paired analysis, group-aware bootstrap 95% CI。
- **実行順**:
  ```text
  Phase A: v3 Global Screening (10 methods / 120 candidates) 【完了】
  Phase B: Human Validity 200件 + E0 / Canonical Production 準備 【進行中】
  Phase C: Seed 42 Dev で各手法 1 setting 固定 → 3-seed 正式集計 【完了】
  Phase D: Math Canonical Production (30 candidates: Linear FULL_REUSE, 非Linear remerge)
  Phase E: 30 candidates + reference models (Safety 4, XSTest, Math 2, General 4)
  Phase F: Gate 0–4 による正式 Math E1 確定
  Phase G: E2 重み空間特性解析
  Phase H: E3 因果介入実験
  Phase I: SafetyFT 2×2 ablation
  Phase J: Code / Medical replication
  Phase K: 必要に応じた E4 (新手法設計) / E5 (独立検証)
  ```
