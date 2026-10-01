# Implementation Plan: Utility FT 性能向上と専用スクリプト作成

## 1. 考察: なぜ Utility FT でベースモデルよりスコアが上がらないのか？
現在の `run_lora_ft.py` やテンプレートの処理内容、および評価結果（Finance OOD/ID、Coding OODの低下や伸び悩み）を調査した結果、以下の3点が原因であると考えられます。

### ① Chat Template の不整合 (最重要)
- `chat_template_utils.py` の Llama-3 用カスタムテンプレートに、必須であるはずの `<|begin_of_text|>` (BOSトークン) が含まれていません。
- Llama-3 は事前学習・指示学習において先頭の BOS トークンを強く前提としたアテンション (Attention Sink) を形成します。これを欠いた状態で学習（Fine-Tuning）すると、モデルの一般的な指示追従能力や推論能力が大きく壊れ、MMLUなどのスコア低下（Catastrophic Forgetting）を引き起こします。

### ② 学習率 (Learning Rate) が高すぎる
- 現在の学習では `target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]` と、ほぼ全ての線形層を LoRA の対象にしています（パラメータ数が多い）。
- 指示学習済みのモデル（Llama-3-8B-Instruct）に対して全ての層を `5e-5` や `2e-5` の学習率でチューニングすると、既存の知識を破壊する（Overfitting）可能性が高くなります。通常、全層LoRAの場合は `1e-5` や `5e-6` など低い学習率が推奨されます。

### ③ エポック数 (Epochs) による過学習
- 現在は `EPOCHS=3` で学習しています。データセットの形式（単純なQ&Aフォーマット）に強く過学習してしまうと、MMLUのような選択肢形式（A, B, C, D）でのゼロショット/フューショット評価の際に、フォーマットを守れなくなり精度が落ちることがあります。

---

## 2. 提案する修正と実装内容

### [MODIFY] テンプレートの修正 (完了)
- `scripts/fine_tuning/chat_template_utils.py` を修正し、Llama-3 のテンプレートの先頭に `{{ bos_token }}` を追加しました。
- ※ 今回は評価スクリプトもこのテンプレートに依存しているため、評価時の精度も改善される（あるいは正当に評価される）はずです。

### [NEW] Utility FT 専用スクリプトの作成 (完了)
- `scripts/fine_tuning/run_utility_ft_only.sh` を新規作成しました。
- `run_phase2.sh` から Safety の学習や評価（advbench, harmbench, xstest 等）を取り除き、以下のプロセスのみを実行するシンプルな構成にしました。
  1. `utility_lora` (Finance) の学習と評価 (MMLU / ID ROUGE)
  2. `coding_lora` (Coding) の学習と評価 (HumanEval, MBPP / ID ROUGE)
- スクリプト内のデフォルト設定として、`LR=1e-5`、`EPOCHS=1` を採用し、引数で上書き可能にしました。
