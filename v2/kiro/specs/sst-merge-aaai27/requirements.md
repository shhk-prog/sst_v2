# AAAI-27 実験計画要件書 (Requirements Spec) - 最終決定版

本要件書は、SST-Mergeの優位性をトップ会議（AAAI-27）レベルの科学的・統計的厳密さで証明するために必要な、実験の要件および採択基準（Acceptance Criteria）を定義するものです。

---

## 1. 実験の対象と目的

SST-Mergeは、安全パッチ適用（Secure Merge）における「Safety-Utility trade-off」（Safety Tax）に対し、FIM（Fisher情報行列）とGEVP（一般化固有値問題）に基づく「方向選別」による安全領域の最大化を提案します。
本実験の目的は、提案手法（SST-Merge）およびそのデータフリー近似（Data-Free SST）が、既存のすべてのマージ手法および baseline 手法と比較して、統計的に有意に優れたパレート境界（Pareto frontier）を描くことを示すことです。

### 対象ベースモデル
- **Meta-Llama-3.1-8B-Instruct** (必須、メインモデル)
- **Mistral-7B-Instruct** (必須級)
- **Qwen2.5-7B-Instruct** または **Qwen2.5-14B-Instruct** (強く推奨)
- **Llama-2-7B-Chat** (先行研究比較用に任意)


---

## 2. 必須比較手法

AAAI-27 における査読に対応するため、以下の 5 つの区分からすべての比較手法を網羅して実行します。

### A. 基本 Baseline 手法
- **Task Arithmetic**: タスクベクトルの単純線形平均。
- **TIES-Merging**: 符号衝突を解消したマージ。
- **DARE**: 確率的ドロップと再スケーリングを用いたマージ。

### B. 近年の高度マージ Baseline 手法
- **DELLA**: MAGPRUNEを用い、DAREやTIESを超える性能を示すスパースマージ手法。
- **Model Breadcrumbs**: 重要なパラメータマスクを選別してマージする手法。

### C. Fisher / 曲率に基づくマージ手法
- **Fisher-weighted averaging**: パラメータの保護にのみ FIM を用いる手法（単一 Fisher 利用との明確な性能差を示すため必須）。
- **RegMean** または **Fisher Mask Nodes**: 共分散または曲率計量を用いて合成時の干渉を抑制する手法。

### D. Safety-Aware マージ手法
- **MergeAlign**: ドメインとアライメントの補間による Safety-Utility トレードオフの調整。
- **SafeMERGE**: Fine-tuning 後の安全性を層選択的マージで保持する手法。
- **LED-Merging**: Safety-Utility の干渉を活性化または重みで直接分離する手法。
- **AlignMerge**: Fisher-Rao 計量と Alignment subspace を用いる手法。

### E. 非マージ (Non-merge) および Guardrail Baseline
- **Safety LoRA のみ**: 安全学習のみを行った場合の上限・下限の確認。
- **Utility LoRA のみ**: 一般性能のみを考慮した場合の上限・下限の確認。
- **Mixed SFT (再学習ベースライン)**: UtilityとSafetyデータを混合してSFTしたモデル。マージを行わない場合との計算コスト・性能比較。
- **Llama Guard / External classifier**: 推論時ガードレール（補助比較）。

---

## 3. 手法内アブレーション (Ablation Study)

提案手法 SST-Merge の各構成要素の有効性を実証するため、以下の 11 項目についてアブレーションを必須とします。

1. **F_h / F_b Ratio (SST本体)**: 提案する一般化レイリー商最適化。
2. **F_h only**: 有害分布の感度 $F_h$ のみによる選別（$F_b$ の必要性の検証）。
3. **1 / F_b only**: 有害分布を無視し、Utilityの保護感度 $F_b$ のみによる選別（$F_h$ の必要性の検証）。
4. **|\Delta_s| top-k (Magnitude)**: FIM比ではなく、タスクベクトルの絶対値の大きさによる選別との比較（FIM比の有効性の検証）。
5. **Random mask**: マスク選択をランダムにした対照実験。
6. **Hard mask vs Soft mask**: 境界ギャップ指標 $\delta_k$ に基づく Top-$k$ 閾値選別とシグモイド連続選別の安定性比較。
7. **Additive vs Interpolation**: 加算モードと補間モードにおけるトレードオフ性能の比較。
8. **Layer-wise prior あり / なし**: lm_head, Attention, FFN に事前重みバイアスを付与することの有無による影響の検証。
9. **Data-Free SST vs FIM-SST**: 実データを使わないタスクベクトル二乗比 surrogate の近似誤差と性能トレードオフの検証。
10. **FIM sample size**: サンプルサイズ $N \in \{50, 100, 500, 1000\}$ による推定精度と性能の関係性の検証。
11. **Harmful / Benign の入れ替え (Negative Control)**: 有害と良性の Fisher 計量を意図的に逆にしてマージを行い、性能が極端に崩壊することを確認する理論的健全性テスト。

> [!IMPORTANT]
> アブレーションにおいて、**F_h/F_b vs F_h only vs magnitude (|\Delta_s| top-k)** の比較は最重要であり、提案する幾何学的方向選別の有効性を実証する上で必須の検証項目です。

---

## 4. 評価データセット・ベンチマークの最低構成

### 4.1 Safety / Jailbreak 評価
- **主表 (Primary Tables) で用いる主要ベンチマーク**:
  - **HarmBench**: Automated red teaming の標準ベンチマーク。ASRおよび有害スコアを測定。
  - **JailbreakBench (JBB)**: 脱獄評価の堅牢性を保証するオープンベンチ。JBB-Behaviorsを含む。
  - **StrongREJECT**: 厳格な自動評価器と言い換えプロンプトを含む強固な評価ベンチ。
- **補助表 (Secondary Tables) または Appendix で用いる補助ベンチマーク**:
  - **WildJailbreak / WildTeaming**: 野生の攻撃戦術を含む実運用向けの頑健性評価。
  - **AdvBench**: 敵対的プロンプトの古典的ベンチマーク（比較用）。
  - **HELM-Safety**: 複数リスクカテゴリで広く評価できるベンチマーク。
  - **XSTest (benign safety prompts)**: 無害プロンプトをどれだけ過剰に拒否しているか (Over-refusal rate) を検証するためのベンチマーク。

### 4.2 Utility 評価
- **標準能力評価ベンチマーク (必須最低構成)**:
  - **MMLU-Pro**: 10択の難関推論問題（難易度が高く性能差が出やすい）。
  - **MMLU**: 先行研究との比較用。
  - **IFEval**: 指示追従（Instruction following）能力の劣化を自動評価。
  - **GSM8K / MATH-500**: 数学および高度推論の保持を確認。
  - **HumanEval / MBPP**: コーディング能力（Python pass@1）の保持確認。
  - **AlpacaEval 2**: オープンな対話品質 (Length-bias 補正済み LC win rate)。
  - **MT-Bench**: LLM judge score によるマルチターン会話能力。
  - **RepliQA / Alpaca**: 既存実験（A5/A6モデル）との整合性を測る QA/指示追従 ROUGE 評価。

---

## 5. データ役割分離 (Data Split Policy)

FIM推定用データが評価用ベンチマークデータと重複し「評価データのカンニング」となるのを防ぐため、以下の通り役割を分離します。

| 用途 | データセット |
|---|---|
| **F_h (Harmful Fisher) 推定** | Custom Jailbreak / BeaverTails train dataset |
| **F_b (Benign Fisher) 推定** | RepliQA train / Alpaca train dataset |
| **Safety 評価用ベンチマーク** | HarmBench, JailbreakBench, StrongREJECT, WildJailbreak |
| **Utility 評価用ベンチマーク** | MMLU-Pro, IFEval, GSM8K, MBPP, AlpacaEval 2 |

---

## 6. 主要指標 (Metrics) と統計的報告

### 5.1 主要指標の定義
AAAI 本文の主表および Pareto 分析では以下の指標を用います。
- **Jailbreak ASR ↓ / Resistance ↑**: 脱獄防御成功率。
- **Over-refusal Rate ↓**: 無害入力への過剰な拒絶応答の割合 (XSTestで測定)。
- **Inference Collapse Rate ↓**: 出力ループ等の発生頻度。
- **Safety@95% Utility ↑**: Utility 性能の低下を 5% 以内に抑えたときの最大安全性能 (主表の核となる指標)。
- **Utility@Target-ASR ↑**: ASR を特定閾値（例: 5%以下）にした際の Utility スコア。
- **Pareto AUC ↑**: $\alpha$ スイープから描かれる Pareto frontier の下部面積。

### 5.2 主表のフォーマット

```text
Method | HarmBench ASR↓ | JBB ASR↓ | StrongREJECT↓ | MMLU-Pro↑ | IFEval↑ | AlpacaEval↑ | Safety@95% Utility↑ | Pareto AUC↑
```

### 5.3 統計的報告要件
- 主要な実験は**最低 3 シード**で実行すること。
- 結果は **mean ± std** で提示すること。
- **95% Bootstrap 信頼区間 (CI)** および **Paired bootstrap test** を用い、SST-Merge と比較手法間の Pareto AUC および Safety@95% Utility の差が統計的に有意であることを示すこと。
