# モデルマージ関連研究の調査報告

ユーザーから指定された10件の論文について、PDFの内容からテキスト情報を抽出し、「マージされているモデルの種類（既存モデルか、論文内でFTしているか）」、「モデル名」、「FTデータセットおよびハイパーパラメータ」を調査しました。

## 調査結果概要

多くのアプローチでは、**すでに公開されている既存のFine-Tuned（指示学習済み・タスク特化型）モデルをそのまま利用してマージする手法（Task Arithmeticなど）**と、**ベースモデルを自作のデータセットでFTしてからマージする手法**の両方が採用されています。

---

### 1. [LREC 2024](https://aclanthology.org/2024.lrec-main.647.pdf) (Fisher-Weighted Merging)
- **モデル**: 既存のモデル
- **モデル名**: `BERT (tiny, base, large)`, `RoBERTa (base)`
- **詳細**: GLUEベンチマークの各タスク（MNLI, SST-2, MRPC, QQP, QNLI, RTE）で既にファインチューニングされたHuggingFace上の公開チェックポイント（例: `M-FAC/bert-tiny-finetuned-mnli`など）をダウンロードしてマージしています。

### 2. [OpenReview](https://openreview.net/pdf?id=uV8LGh2DCx) (DRIFT-MEDIAN)
- **モデル**: 論文内でFTしているモデル ＋ 既存のモデル
- **モデル名**: `Llama-3.1-8B`, `Llama-3.2-3B`, `Llama-2-7b`, `GPT-2`, `CLIP-ViT-B/32`
- **FTデータセット**: 数学(MATH, GSM8K)、安全性(Harmbench, XSTest)、GLUEタスクなど
- **ハイパーパラメータ等**: モデルごとに各タスク（数学、コーディング、マルチリンガル）でFTし、マージを行っています。

### 3. [NAACL 2025](https://aclanthology.org/2025.naacl-long.254.pdf)
- **モデル**: 論文内でFTしているモデル
- **モデル名**: `T5-base`, `T5-large`
- **FTデータセット**: QASC, Quartz, Story Cloze, Wiki QA, Winograndeなど
- **ハイパーパラメータ**: Batch Size = 64, Learning Rate = $1 \times 10^{-4}$, Training Steps = 2,500（AdamW）

### 4. [NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/file/70c26937fbf3d4600b69a129031b66ec-Paper-Conference.pdf) (Editing Models with Task Arithmetic)
- **モデル**: 論文内でFTしているモデル ＋ 既存モデル
- **モデル名**: `RoBERTa-base`, `BERT-base`, `GPT-2`, `GPT-J`
- **FTデータセット**: IMDB, SST-2, RTE, Civil Comments (Toxicity除去のため)
- **ハイパーパラメータ**: Batch Size = 16 または 128, Learning Rate = $1 \times 10^{-5}$ 〜 $1 \times 10^{-4}$ (AdamW), 1〜5 epochs

### 5. [arXiv:2310.12808](https://arxiv.org/pdf/2310.12808) (DARE等)
- **モデル**: 既存のモデル
- **モデル名**: `LLaMA`ベースの既存タスクモデル (`Alpaca`, `WizardLM` 等) や `T5`など
- **詳細**: 個別タスクで公開されているモデル同士（Homologous Models）をパラメータ空間でマージし、能力を結合できるかを検証しています。

### 6. [arXiv:2603.21705](https://arxiv.org/pdf/2603.21705) (Task Alignment/SafeMerge)
- **モデル**: 論文内でFTしているモデル
- **モデル名**: `LLaMA-3-8B`, `Mistral-7B` など
- **FTデータセット**: Anthropic HH (アライメント), Alpaca (タスク)
- **ハイパーパラメータ**: ミニバッチサイズ = 32（SVDアップデート時）, Batch Size = 512 (K-means), Cosine Distance, ピークLRの10%へCosine Decay

### 7. [arXiv:2512.16245](https://arxiv.org/pdf/2512.16245) (MERGEALIGN)
- **モデル**: 論文内でFTしているモデル
- **モデル名**: `Llama-3`系（Instruction Pre-trained）
- **FTデータセット**: 医学(Medicine), 金融(Finance), HH-RLHF (7,000サンプル)
- **ハイパーパラメータ**: Preference Trainingにおいて Batch Size = 12 (device size 2 + grad acc 6), Learning Rate = 8e-06, 3 epochs, LoRA rank 16, alpha 32, warmup steps 150

### 8. [arXiv:2411.06824](https://arxiv.org/pdf/2411.06824) / 9. [ACL 2025/2024](https://aclanthology.org/2024.acl-long.1055.pdf) (LED-Merging)
*(※ ACLのURLは2024版として特定しました)*
- **モデル**: 既存のモデル（公開されている特化モデルをそのまま使用）
- **モデル名**: `Llama-3-8B`系 (`Meta-Llama-3-8B-Instruct`, `MAmmoTH2-8B-Plus`, `Replete-Coder-Llama3-8B`), `Mistral-7B`系 (`MetaMath-Mistral`, `WizardMath`など), `Llama-2-13B`系
- **詳細**: 安全性モデル、数学特化モデル、コード生成モデルといった既存の各特化モデル（ベースモデルが同じもの）を収集し、干渉（Interference）を排除するマージ手法を提案しています。FTは行わず、既存のチェックポイントを利用。

### 10. [arXiv:2503.17239](https://arxiv.org/pdf/2503.17239) (SafeMERGE)
- **モデル**: 論文内でFTしているモデル（LoRA使用）
- **モデル名**: `Llama-2-7B-Chat`, `Llama-3.1-8B-Instruct`, `Qwen-2-7B-Instruct`
- **FTデータセット**: GSM8K (数学), PubMedQA (医学), AdvBench/HarmfulQA (有害性FT)
- **ハイパーパラメータ**:
  - GSM8K: Batch Size = 32, Learning Rate = 1e-4 (Linear Schedule), 6 epochs, LoRA Rank 16
  - PubMedQA: Batch Size = 64, Learning Rate = 1e-4 (Cosine Schedule), 2 epochs
  - Harmful Fine-Tuning: Batch Size = 32, Learning Rate = 1e-4, 5 epochs

---

## 結論と傾向

関連研究では、大きく分けて以下の2パターンの実験構成が取られています。
1. **「Task Arithmetic」や「LED-Merging」系**: HuggingFaceなどで公開されている、**すでに特定のドメインでFine-Tuningされた既存モデル**（`MAmmoTH2`, `WizardMath`, `Instruct`系など）をダウンロードし、そのままマージして性能を検証。
2. **「SafeMERGE」や「MERGEALIGN」系**: ベースモデルに対して、論文の著者が自ら**特定のタスクデータセット（GSM8K, PubMedQA, Alpaca, HH-RLHFなど）とハイパーパラメータ（LR 1e-4〜8e-6前後, Batch Size 12〜64）を用いてLoRA等でFine-Tuning**し、生成されたタスク特化アダプタ（またはフルパラメータ）をマージする。
