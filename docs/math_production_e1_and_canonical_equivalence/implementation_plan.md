# 実装計画書: Math Production E1 比較実験および正規化振る舞い等価性実証 (E0c)

## 1. 目的
Math Pilot の成功（実測値による全段接続）を受け、統計的に意味のある本番評価規模へ拡張する。
同時に、語彙正規化（32001 -> 32000）がモデルの本来の推論能力を一切変化させていないことを数学的・実証的に証明（E0c 振る舞い等価性検証）する。

## 2. 実装コンポーネント詳細

### 2.1 E0c: Canonicalization Behavioral Equivalence Test (`test_canonical_equivalence.py`)
- **対象**:
  - Original WizardMath vs Canonical WizardMath
  - Original SafetyFT vs Canonical SafetyFT
- **入力条件**:
  - `input_ids < 32000`
  - `sequence_length <= 2048`
- **測定指標**:
  - `max_abs_logit_diff`: first 32000 logits の最大絶対誤差（浮動小数点の丸め誤差レベル $\approx 0$ であるべき）
  - `mean_abs_logit_diff`: 平均絶対誤差
  - `argmax_agreement`: 最も確率の高いトークンの完全一致率（100.0% であるべき）
  - `generation_exact_match`: Greedy 生成結果の完全一致
- **出力**: `v4/results/models/canonical/e0c_behavioral_equivalence_report.json`

### 2.2 Standalone Reference Evaluator (`eval_standalone_references.py`)
- **対象モデル**:
  - Math Standalone (WizardMath)
  - Safety Standalone (SafetyFT)
  - Base Model (Llama-2-7b-hf)
- **評価内容**:
  - 同一有害プロンプト（HarmBench, JailbreakBench, StrongReject, WildJailbreak）
  - 同一無害プロンプト（XSTest / AlpacaEval 由来）
  - 同一数学ユーティリティ（GSM8K, MATH500）
- **成果物**:
  - 実測 `baseline_overrefusal`（WizardMath 単体の無害質問に対する過剰拒否率）の確定
  - 単体能力（utility 100% 基準点および safety 基準点）の実測値の固定

### 2.3 Math Production E1 Runner (`run_math_production_e1.py`)
- **対象手法**: Linear Safety-Patch ($\theta_m = \theta_u + \alpha(\theta_s - \theta_u)$)
- **探索空間**: $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$（seed 42）
- **評価項目**:
  - ASR_all, ASR_valid, VRR harmful, VRR benign
  - Over-refusal および Margin（実測 WizardMath baseline との差）
  - Utility Score（GSM8K / MATH500）および WizardMath 単体に対する相対比
- **選定**: `e1_selector.py::evaluate_feasible_region_strict` による厳格判定
