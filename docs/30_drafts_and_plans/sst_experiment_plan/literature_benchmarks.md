# 先行研究10本の評価ベンチマーク・比較手法一覧

ご提示いただいた10本の先行研究それぞれについて、論文内で使用されている評価データセット・ベンチマーク、および比較対象とされているベースライン手法を抽出・整理しました。

---

### 1. Fisher Mask Nodes for Language Model Merging (LREC 2024)
- **URL**: [aclanthology.org/2024.lrec-main.647.pdf](https://aclanthology.org/2024.lrec-main.647.pdf)
- **評価データセット・ベンチマーク**:
  - NLP (GLUE Benchmark): MNLI, SST-2, MRPC, QQP, QNLI, RTE
- **比較手法 (Baselines)**:
  - Simple Averaging (単純平均)
  - Fisher-Weighted Averaging (FWA / Matena & Raffel, 2022)

---

### 2. Task-Aware Model Merging via Fisher-Weighted Median (OpenReview 2025)
- **URL**: [openreview.net/pdf?id=uV8LGh2DCx](https://openreview.net/pdf?id=uV8LGh2DCx)
- **評価データセット・ベンチマーク**:
  - GLUE: CoLA, MNLI, MRPC, QNLI, QQP, RTE, SST2
  - その他、数学、コーディング、多言語推論、安全性、視覚タスクなど。
  - 主要指標: PRR (Performance Retain Rate)
- **比較手法 (Baselines)**:
  - Simple Averaging, Task Arithmetic, TIES-Merging, DARE
  - Localize-and-Stitch, Fisher Merging, PCB-Merging

---

### 3. Dynamic Fisher-weighted Model Merging via Bayesian Optimization (NAACL 2025)
- **URL**: [aclanthology.org/2025.naacl-long.254.pdf](https://aclanthology.org/2025.naacl-long.254.pdf)
- **評価データセット・ベンチマーク**:
  - NLP推論・QA: PAWS, QASC, QuaRTz, Story Cloze, WikiQA, Winogrande
- **比較手法 (Baselines)**:
  - Task Arithmetic, TIES等のパラメータスケーリング手法
  - 標準的な重み付けマージ（Simple Averaging）

---

### 4. Merging Models with Fisher-Weighted Averaging (NeurIPS 2022)
- **URL**: [proceedings.neurips.cc/paper_files/...](https://proceedings.neurips.cc/paper_files/paper/2022/file/70c26937fbf3d4600b69a129031b66ec-Paper-Conference.pdf)
- **評価データセット・ベンチマーク**:
  - NLP: RTE, MRPC, SST-2
  - Vision (OODロバスト性): ImageNet-A, ImageNet-R, ImageNet Sketch, ImageNet V2, ObjectNet
- **比較手法 (Baselines)**:
  - Isotropic Merging (パラメータの単純平均)
  - Output Ensembling (出力のアンサンブル)

---

### 5. Model Merging by Uncertainty-Based Gradient Matching (Arxiv 2023)
- **URL**: [arxiv.org/pdf/2310.12808](https://arxiv.org/pdf/2310.12808)
- **評価データセット・ベンチマーク**:
  - 感情分析タスク: IMDB, Yelp, RT, SST2, Amazon
- **比較手法 (Baselines)**:
  - Task Arithmetic (TA)

---

### 6. Data-Free Layer-Adaptive Merging via Fisher Information / FIM-TIES (Arxiv 2026想定/最新)
- **URL**: [arxiv.org/pdf/2603.21705](https://arxiv.org/pdf/2603.21705)
- **評価データセット・ベンチマーク**:
  - 数学推論: GSM8K, MATH500, Minerva Math, OlympiadBench, CollegeMath, AIME24
- **比較手法 (Baselines)**:
  - Task Arithmetic, TIES-Merging
  - AIM, Sens-Merging, ACM-TA, ACM-TIES

---

### 7. AlignMerge: Geometric Alignment Protection (Arxiv 2025)
- **URL**: [arxiv.org/pdf/2512.16245](https://arxiv.org/pdf/2512.16245)
- **評価データセット・ベンチマーク**:
  - 指示追従・推論タスク (Utility)
  - 毒性スコア (Toxicity rate) および LLM-as-a-Judge による安全性評価
- **比較手法 (Baselines)**:
  - SafeMerge, MergeAlign, SALSA
  - Euclidean Interpolation, Layer-wise Interpolation

---

### 8. MERGE ALIGN: Safety Alignment of Domain-Expert Models (Arxiv 2024)
- **URL**: [arxiv.org/pdf/2411.06824](https://arxiv.org/pdf/2411.06824)
- **評価データセット・ベンチマーク**:
  - 安全性: BeaverTails (MD-Judgeを用いた判定)
  - 専門ドメイン (Utility): 医学 (Medicine)、金融 (Finance)
- **比較手法 (Baselines)**:
  - ORPO (Preference Optimization による再学習)
  - Slerp (Spherical Linear Interpolation), Full Model Interpolation

---

### 9. LED-Merging: Non-interfering Parameter Conflict Resolution (ACL 2025)
- **URL**: [aclanthology.org/2025.acl-long.1055.pdf](https://aclanthology.org/2025.acl-long.1055.pdf)
- **評価データセット・ベンチマーク**:
  - 安全性: HarmBench, SORRY-Bench
  - 数学・コーディング: GSM8K, MATH, MBPP, HumanEval-Pack
- **比較手法 (Baselines)**:
  - Task Arithmetic, Ties-Merging
  - Model Stock, Model Breadcrumbs

---

### 10. SafeMERGE: Selective Layer-Wise Merging (Arxiv 2025)
- **URL**: [arxiv.org/pdf/2503.17239](https://arxiv.org/pdf/2503.17239)
- **評価データセット・ベンチマーク**:
  - Utility: GSM8K, PubMedQA, TeleData, TeleQnA, TSpecLLM
  - 安全性 (Red-teaming): DirectHarm, HexPhi (Llama-Guard-3-8Bによる判定)
- **比較手法 (Baselines)**:
  - SafeInstruct, SafeLoRA
  - Linear Merging (通常の線形マージ)

---

### まとめと考察
これらの論文群から、近年（2024〜2025年以降）のモデルマージ研究は、単純なGLUEタスクによる性能評価から、**「数学・コーディング能力（GSM8K, MATH500等）」と「安全性（HarmBench, DirectHarm等）」のトレードオフ検証**へと評価の軸が移行していることが分かります。
また、比較手法としても Task Arithmetic や TIES-Merging が標準的なベースラインとして定着しており、最新手法はこれらに加えて「SafeMERGE」や「AlignMerge」等の**安全性保護に特化したマージ手法**との比較を行っているのが特徴です。
