# モデルマージおよび安全性アライメントに関する論文の調査レポート (Baseline & Evaluation)

## 概要
本レポートは、モデルマージ（Model Merging）およびファインチューニングに伴う安全性アライメント低下の抑制に関する10本の論文について、再現実験における**比較Baseline手法**、**評価設定（ベースモデル、評価データセット、指標など）**、および**公式コードの有無**を調査・整理したものです。

---

## 1. 公式コードが存在する論文

### 1.1 Merging Models with Fisher-Weighted Averaging (NeurIPS 2022)
- **著者:** Michael Matena, Colin Raffel
- **URL:** [Paper PDF](https://proceedings.neurips.cc/paper_files/paper/2022/file/70c26937fbf3d4600b69a129031b66ec-Paper-Conference.pdf)
- **公式コード:** [mmatena/model_merging](https://github.com/mmatena/model_merging)
- **提案手法:** パラメータごとの対角Fisher情報行列（Diagonal Fisher Information Matrix）を重要度重みとして、同一の事前学習から派生した複数の専門モデルをデータなしで重み付き平均マージする手法。
- **再現実験における比較 Baseline 手法:**
  - **Isotropic Averaging (Simple Averaging):** パラメータの単純な均等重み付き平均化。
  - **Standard Fine-tuning:** 中間タスク（Intermediate-task）学習など、通常の勾配ベースのマルチタスクファインチューニング。
  - **Single-task Experts:** マージを行わない各タスク特化の単一モデル。
- **評価（Evaluation）設定:**
  - **評価モデル:** T5-Base, T5-Large
  - **評価データセット:** GLUE ベンチマーク（MNLI, SST-2, QQP などのテキスト分類タスク）および中間タスク転移設定。
  - **評価指標:** 各分類タスクの精度（Accuracy / F1 スコア）、ゼロショット性能。

### 1.2 Model Merging by Uncertainty-Based Gradient Matching (ICLR 2024)
- **著者:** Nico Daheim, Thomas Möllenhoff, Edoardo Maria Ponti, Iryna Gurevych, Mohammad Emtiyaz Khan
- **URL:** [Paper PDF](https://arxiv.org/pdf/2310.12808)
- **公式コード:** [UKPLab/iclr2024-model-merging](https://github.com/UKPLab/iclr2024-model-merging)
- **提案手法:** マージモデルの性能低下を「勾配の不一致 (Gradient Mismatch)」と理論的に結びつけ、二次近似（ヘシアン/Fisher情報）を用いた「不確実性ベースの勾配マッチング」を行うことで、大規模なTransformerにスケール可能なマージを提案。
- **再現実験における比較 Baseline 手法:**
  - **Standard Weighted Averaging (Simple Averaging):** 単純なパラメータの平均マージ。
  - **Task Arithmetic:** 各タスク特化の更新ベクトルのスケーリング加算。
  - **Fisher-Weighted Averaging (Matena & Raffel, 2022):** パラメータごとの対角Fisher情報ベースのマージ。
- **評価（Evaluation）設定:**
  - **評価モデル:** LLaMA 等の大規模言語モデル（LLMs）および Vision Transformers (ViTs)。
  - **評価データセット:** GLUE（SST-2, MNLI などの分類）、感情分析、画像分類、および特定の知識を取り除く「モデル編集（Model Editing / 忘却）」タスク。
  - **評価指標:** 分類タスクの精度（Accuracy / F1）、モデル忘却率、ハイパーパラメータの変化に対する頑健性（ロバスト性）。

### 1.3 Fisher Mask Nodes for Language Model Merging (LREC-COLING 2024)
- **著者:** Thennal D K, Ganesh Nathan, Suchithra M S
- **URL:** [Paper PDF](https://aclanthology.org/2024.lrec-main.647.pdf)
- **公式コード:** [thennal10/fisher-nodes-merging](https://github.com/thennal10/fisher-nodes-merging)
- **提案手法:** Fisher-Weighted Averaging の計算コスト（全パラメータのFisher情報を保持・計算する負荷）を解消するため、Attention Head や FFN レイヤーの mask node に対してのみ対角Fisher情報を算出してマージの重要度重みとする手法。
- **再現実験における比較 Baseline 手法:**
  - **Isotropic Averaging (Simple Averaging):** 単純なパラメータ平均。
  - **Task Arithmetic:** タスク更新ベクトルの加算。
  - **Fisher-weighted averaging (Matena & Raffel, 2022):** 全パラメータの対角Fisher情報を重みとするマージ。
- **評価（Evaluation）設定:**
  - **評価モデル:** BERT-base, RoBERTa-base
  - **評価データセット:** GLUE ベンチマーク (SST-2, MNLI, QQP, QNLI など)
  - **評価指標:** タスクごとの精度（Accuracy / F1）、およびマージ時の計算コスト・実行時間（元のFisherマージに対して約57〜321倍の高速化を実証）。

### 1.4 Dynamic Fisher-weighted Model Merging via Bayesian Optimization (NAACL 2025)
- **著者:** Sanwoo Lee, Jiahao Liu, Qifan Wang, Jingang Wang, Xunliang Cai, Yunfang Wu
- **URL:** [Paper PDF](https://aclanthology.org/2025.naacl-long.254.pdf)
- **公式コード:** [sanwooo/df-merge](https://github.com/sanwooo/df-merge)
- **提案手法:** **DF-Merge**。複数のタスク特化モデルをマージする際、バリデーションデータを用いて各専門モデルのスケーリング係数をベイズ最適化（BO）で動的に探索し、各探索イテレーションでFisher情報を統合してマージを行う手法。
- **再現実験における比較 Baseline 手法:**
  - **Isotropic Averaging (Simple Averaging):** パラメータの単純平均。
  - **Task Arithmetic:** ベクトル加算。
  - **TIES-Merging:** パラメータの競合（符号・重複）を考慮したタスクベクトルのマージ。
  - **DARE:** 微小な更新パラメータをランダムにドロップアウトしてマージする手法。
  - **Fisher-weighted averaging (Matena & Raffel, 2022):** 対角Fisher情報によるマージ。
- **評価（Evaluation）設定:**
  - **評価モデル:** T5-Base, T5-Large
  - **評価データセット:** QA・推論タスク（PAWS, QASC, Quartz, Story Cloze, WikiQA, Winogrande）
  - **評価指標:** マージモデルのAccuracy、最適化に必要なバリデーションデータ量、および収束ステップ数（10〜20ステップで収束）。

### 1.5 LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint (ACL 2025)
- **著者:** Qianli Ma, Dongrui Liu, Qian Chen, Linfeng Zhang, Jing Shao
- **URL:** [Paper PDF](https://aclanthology.org/2025.acl-long.1055.pdf)
- **公式コード:** [MqLeet/LED-Merging](https://github.com/MqLeet/LED-Merging)
- **提案手法:** 専門タスクモデルと安全性アライメントモデルのマージにおける「安全性と実用性（ユーティリティ）の衝突」を防ぐための手法。勾配情報に基づき重要ニューロンを特定（Location）し、複数モデルの重要度を投票で統合（Election）し、排他的にパラメータを隔離（Disjoint）してマージを行う。
- **再現実験における比較 Baseline 手法:**
  - **Task Arithmetic (TA):** 標準的なタスクベクトルの加算。
  - **TIES-Merging:** 符号の不一致を解決するマージ。
  - **DARE:** ドロップアウトを用いたマージ。
  - **SafeMerge / MergeAlign:** アライメント安全性の保護を目的とする既存の統合手法。
- **評価（Evaluation）設定:**
  - **評価モデル:** Llama-3-8B, Mistral-7B, Llama2-13B
  - **評価データセット:**
    - 安全性: HarmBench, SORRY-Bench
    - 有用性（ユーティリティ）: GSM8K (数学), HumanEvalPack (コーディング)
  - **評価指標:** 有害回答率（Harmful response rates）の低減率、および数学・コーディングタスクの精度（Accuracy / Pass@1）。

### 1.6 SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging (2025-2026)
- **著者:** Aladin Djuhera, Swanand Ravindra Kadhe, Farhan Ahmed, Syed Zawad, Holger Boche
- **URL:** [Paper PDF](https://arxiv.org/pdf/2503.17239)
- **公式コード:** [aladinD/SafeMERGE](https://github.com/aladinD/SafeMERGE)
- **提案手法:** ドメイン特化のファインチューニングによって安全性が低下したモデルに対し、追加の訓練なしでレイヤーごとにマージを適用する手法。安全アライメント部分空間とモデル各層の活性化値とのコサイン類似度を測定し、安全性が乖離した層（レイヤー）のみを選択的に安全アライメントモデルとマージする。
- **再現実験における比較 Baseline 手法:**
  - **RESTA / RESTA-Instruct:** 表現空間（Representation-space）におけるアライメント保存手法。
  - **SafeLoRA:** 特異値分解等を応用したLoRAファインチューニング時のアライメント保護手法。
  - **Standard model merging:** Task Arithmetic、およびパラメータの単純な線形補間（Interpolation）。
- **評価（Evaluation）設定:**
  - **評価モデル:** Llama-2, Llama-3.1, Qwen-2, Qwen-2.5 などの各種サイズ
  - **評価データセット:**
    - 安全性: AdvGLUE, HarmBench, BeaverTails
    - 有用性: GSM8K, ARC, MMLU などの標準ベンチマーク
  - **評価指標:** 有害出力の発生率（Harmful output rates）、および下流ベンチマークの正解率（Accuracy）。

---

## 2. 公式コードが存在しない（または未公開の）論文

### 2.1 Task-Aware Model Merging via Fisher-Weighted Median (ICLR 2026, withdrawn)
- **著者:** Baban Gain, et al.
- **URL:** [Paper PDF](https://openreview.net/pdf?id=uV8LGh2DCx)
- **公式コード:** なし（ICLR 2026 投稿後に取り下げられたため、公式の公開リポジトリは未確認）
- **提案手法:** **DRIFT-MEDIAN**。タスクベクトルの干渉（符号の対立やパラメータの冗長性）を緩和するステップと、Fisher情報量に基づく感度重み付けを統合。外れ値パラメータの悪影響を低減するため、対角Fisher情報を考慮した「重み付き中央値（Weighted Median）」によるパラメータ集約を行う。
- **再現実験における比較 Baseline 手法:**
  - **Simple Averaging:** 単純な平均マージ。
  - **Task Arithmetic:** タスクベクトルの線形補間。
  - **Fisher-weighted merging:** パラメータごとのFisher加重平均。
  - **TIES-Merging:** パラメータの符号調整と枝刈りを行うマージ。
  - **DARE:** ランダムドロップアウトを用いたマージ。
  - **PCB (Parameter-wise Consensus-based merging):** 符号一致に基づいてマージする手法。
- **評価（Evaluation）設定:**
  - **評価モデル:** Llama-3.1-8B, Llama-3.2-3B, Llama-2-7B, GPT-2, CLIP-ViT-B/32
  - **評価データセット:** 数学（GSM8K, MATH）、コーディング（HumanEval, MBPP）、多言語理解、安全性アライメント（BeaverTails, SafeLoRA）、および画像分類。
  - **評価指標:** 各専門モデルの性能維持率を示す **PRR (Performance Retain Rate)**、および各下流タスクの精度（Accuracy / F1）。

### 2.2 Data-Free Layer-Adaptive Merging via Fisher Information for Long-to-Short Reasoning LLMs (2026)
- **著者:** Tian Xia
- **URL:** [Paper PDF](https://arxiv.org/pdf/2603.21705)
- **公式コード:** なし（論文の記述では「採択後にコードを公開予定」となっており、現時点では公式の公開リポジトリは無し）
- **提案手法:** **FIM-Merging (FIM-TIES / FIM-TA)**。基本モデルと長いChain-of-Thought（CoT）を行う推論特化LLMをマージする際、出力トークン長を大幅に削減（約92%）しつつ推論性能を保持するための手法。マージ誤差の境界が各層のヘシアンノルムに依存することに着目し、キャリブレーションデータ不要でランダムトークンから推定した対角Fisher情報（FIM）を層ごとのスケーリング係数（$\alpha_l$）に適用する。
- **再現実験における比較 Baseline 手法:**
  - **ACM-TIES / ACM-TA (Adaptive Coefficient Merging):** バリデーションデータを用いて進化的アルゴリズム等で層ごとの係数を最適化する既存手法。
  - **TIES-Merging / Task Arithmetic (TA) / DARE:** レイヤーごとに一様（Uniform）な係数を使用する標準的なマージ手法。
- **評価（Evaluation）設定:**
  - **評価モデル:** Qwen-2-1.5B, Qwen-2-7B, Llama-3-8B などのスケール
  - **評価データセット:** L2S (Long-to-Short) 推論ベンチマーク、MATH500、AIME24
  - **評価指標:** 推論の正答率（MATHスコア、AIMEスコアなど）、生成された回答の平均トークン長さ、およびキャリブレーションデータの必要性。

### 2.3 AlignMerge - Alignment-Preserving Large Language Model Merging via Fisher-Guided Geometric Constraints (2025)
- **著者:** 不明（プリプリントにつき著者名未取得）
- **URL:** [Paper PDF](https://arxiv.org/pdf/2512.16245)
- **公式コード:** なし（現時点で直接の公式公開リポジトリは未公開）
- **提案手法:** モデルマージがモデルの「安全性アライメント（調和）」を著しく損ねる現象に対処するため、マージを単なるパラメータの数値処理ではなく「幾何学的な制約問題」として定義する。事前アライメント済みのベースモデルの周囲に局所的なFisher情報に基づく空間（Fisher chart）を想定し、アライメント部分空間（Alignment subspace）からマージパラメータが逸脱するのを防ぐ制約（プロジェクト行列など）を課して最適化を行う。
- **再現実験における比較 Baseline 手法:**
  - **Fisher Soups (Fisher-Weighted Averaging):** 標準的な対角Fisher加重平均。
  - **TIES-Merging:** パラメータ干渉を緩和するマージ。
  - **SafeMerge:** 安全性アライメントを保持するための先行手法。
  - **MergeAlign:** ドメインベクトルとアライメントベクトルを統合するマージ手法。
- **評価（Evaluation）設定:**
  - **評価モデル:** LLaMA-3 8B, Mistral 7B, Qwen 2, Phi-3.5, Gemma 2
  - **評価データセット:** Toxicity, Helpfulness, Instruction-following, Reasoning などのアライメント・アセスメントデータセット。
  - **評価指標:** AQI (Alignment Quality Index)、Toxicity score、LLM-judge による出力アライメント評価、アライメント部分空間のドリフト（Drift）量。

### 2.4 Combining Domain and Alignment Vectors to Achieve Better Knowledge-Safety Trade-offs in LLMs (2024)
- **著者:** Megh Thakkar, Quentin Fournier, Matthew Riemer, Pin-Yu Chen, Amal Zouaq, Payel Das, Sarath Chandar
- **URL:** [Paper PDF](https://arxiv.org/pdf/2411.06824)
- **公式コード:** なし（論文公式のコードは一般公開されていないため「無し」に分類。ただし、著者らは類似したアライメントの評価枠組みとして SEAL や MoLA などのリポジトリとの関連性に言及している）
- **提案手法:** **MergeAlign**。医療や金融などの特定のドメインにファインチューニングされたモデルが、特化能力を得る代償として安全性を失う問題に対処する。ドメイン更新ベクトル（Domain Vector）とアライメント更新ベクトル（Alignment Vector）のパラメータの線形補間（Interpolation）を行い、安全性の回復と専門知識の維持の両立を図る。
- **再現実験における比較 Baseline 手法:**
  - **DPO (Direct Preference Optimization):** 直接好みのデータを学習させる手法。
  - **ORPO (Odds Ratio Preference Optimization):** ファインチューニング中にアライメントを直接制約する手法。
  - **PEFT (LoRA):** LoRAを用いたドメインモデルに対する後からの安全性学習。
  - **Full-model Fine-tuning:** 全パラメータを用いたアライメントチューニング。
- **評価（Evaluation）設定:**
  - **評価モデル:** Llama-3-8B（Medicine-Llama-3-8B, Finance-Llama-3-8B などの特化バリアント）、Qwen-2.5
  - **評価データセット:**
    - 安全性: BeaverTails (Llama-Guard-3による評価)、HH-RLHF の red-team サブセット (MD-Judge-v0.1による評価)
    - ドメイン知識: 医療・金融ドメインに特化した専門能力評価ベンチマーク
  - **評価指標:** 安全性評価スコア（有害判定率）、ドメインタスクの精度（Accuracy）、および「知識と安全性のトレードオフ（Knowledge-Safety Trade-off）」の改善度。

---

## 3. 全体俯瞰・比較表

| 論文タイトル (略称) | 提案手法の特徴 | 主要な比較 Baseline | 評価対象モデル | 評価データセット / ドメイン | 公式コード |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fisher-Weighted Averaging**<br>(NeurIPS 2022) | 対角Fisher情報を重要度重みとしたパラメータマージ | Isotropic (Simple) Avg, Fine-tuning | T5 | GLUE (テキスト分類) | [あり](https://github.com/mmatena/model_merging) |
| **Uncertainty Gradient Matching**<br>(ICLR 2024) | 二次近似で勾配の不一致を緩和する不確実性ベースのマージ | Simple Avg, Task Arithmetic, Fisher Avg | LLMs, ViTs | GLUE, 画像分類, モデル忘却 | [あり](https://github.com/UKPLab/iclr2024-model-merging) |
| **Fisher Mask Nodes**<br>(LREC-COLING 2024) | Attention/FFNのmask nodeのFisher情報を利用した高速マージ | Simple Avg, Task Arithmetic, Fisher Avg | BERT, RoBERTa | GLUE | [あり](https://github.com/thennal10/fisher-nodes-merging) |
| **DF-Merge**<br>(NAACL 2025) | スケーリング係数をベイズ最適化＋Fisher情報で動的マージ | Simple Avg, Task Arithmetic, TIES, DARE, Fisher Avg | T5 | PAWS, QASC, WikiQA などのQA | [あり](https://github.com/sanwooo/df-merge) |
| **LED-Merging**<br>(ACL 2025) | 勾配ベース重要度、投票、パラメータ排他隔離による安全衝突回避 | Task Arithmetic, TIES, DARE, SafeMerge, MergeAlign | Llama-3, Mistral, Llama2 | HarmBench (安全), GSM8K, HumanEval (有用) | [あり](https://github.com/MqLeet/LED-Merging) |
| **SafeMERGE**<br>(2025-2026) | 安全部分空間と層活性の類似度に基づく選択的レイヤーマージ | RESTA, SafeLoRA, Task Arithmetic, Simple Interpolation | Llama-2, Llama-3.1, Qwen-2, Qwen-2.5 | HarmBench (安全), GSM8K, MMLU (有用) | [あり](https://github.com/aladinD/SafeMERGE) |
| **DRIFT-MEDIAN**<br>(ICLR 2026, withdrawn) | 符号/冗長性干渉緩和＋対角Fisher考慮の重み付き中央値集約 | Simple Avg, Task Arithmetic, TIES, DARE, Fisher Avg, PCB | Llama-3.1, Llama-2, GPT-2, ViT | 数学, コード, 多言語, 安全, 画像分類 | なし |
| **FIM-Merging**<br>(2026) | キャリブレーション不要で対角Fisher情報による層係数適応 | ACM-TIES, ACM-TA, TIES, Task Arithmetic, DARE | Qwen-2, Llama-3 | MATH500, AIME24 (推論長さ削減) | なし (採択後公開予定) |
| **AlignMerge**<br>(2025) | 局所Fisher空間内のアライメント部分空間幾何制約マージ | Fisher Soups, TIES, SafeMerge, MergeAlign | Llama-3, Mistral, Qwen 2, Gemma 2 | Toxicity, Helpfulness などの安全・対話 | なし |
| **MergeAlign**<br>(2024) | ドメインベクトルとアライメントベクトルの線形補間 | DPO, ORPO, LoRA, Full-model Fine-tuning | Llama-3, Qwen-2.5 | BeaverTails, HH-RLHF (安全), 医療/金融 | なし |
