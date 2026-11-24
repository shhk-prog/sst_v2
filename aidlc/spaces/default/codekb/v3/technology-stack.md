# 技術スタック: v3

## 言語と実行環境

| 項目 | 内容 |
|---|---|
| 言語 | Python 3（バージョン未固定）、Bash（SLURM スクリプト）、LaTeX（論文） |
| 仮想環境 | `venv_v3`（標準）、`venv_led`（LED-Merging 専用）。どちらも `.gitignore` 対象 |
| ハードウェア | 共有 GPU サーバ（SLURM、`#SBATCH --partition=h100`, `--gres=gpu:1`） |
| 数値精度 | モデルは fp16 で読み込む。Safety SFT は `fp16=True`。mergekit は `dtype: float16`。SST の FIM は、勾配を fp16 で計算し fp32 で累積・保存し、merge 時に fp16 にキャストする（`mergers/fim.py` L21, L61, L161） |

## フレームワークとライブラリ

バージョンは `requirements.txt` の指定どおり。固定されていないものは「未固定」と書く。

| ライブラリ | バージョン | 用途 |
|---|---|---|
| torch | >=2.0.0 | テンソル演算、FIM の勾配 |
| transformers | >=4.38.0 | `AutoModelForCausalLM`, `AutoTokenizer` |
| peft | >=0.9.0 | Safety LoRA、`merge_and_unload` |
| trl | >=0.8.0 | `SFTTrainer`, `SFTConfig` |
| accelerate | >=0.27.0 | 分散と device_map |
| lm-eval | >=0.4.1 | 有用性評価（`simple_evaluate`、vLLM / HF バックエンド） |
| vllm | 未記載 | 安全性の生成と lm-eval の vLLM バックエンド（`--use_vllm`） |
| mergekit | 未固定（`baselines/mergekit` にも gitlink あり） | TIES / DARE / DELLA / linear |
| lm-cocktail | 未固定 | MergeAlign の依存 |
| strong_reject | `evaluators/strong_reject`（gitlink） | StrongREJECT 判定（`finetuned_gemma`） |
| sentence-transformers, langdetect, antlr4-python3-runtime==4.11, sympy, math-verify | — | 評価補助（Math500 の採点など） |
| pandas >=2.0.0, numpy >=1.24.0, scipy >=1.10.0, matplotlib >=3.7.0, pyyaml >=6.0, tqdm >=4.65.0 | — | 集計、可視化、設定 |
| datasets | 未記載 | `data_prep.py` でのデータ取得 |

## 外部モデル（Hugging Face Hub）

| 役割 | モデル ID |
|---|---|
| ベース | `meta-llama/Llama-2-7b-hf` |
| ドメイン | `WizardLMTeam/WizardMath-7B-V1.0`, `vanillaOVO/WizardCoder-Python-7B-V1.0`, `medalpaca/medalpaca-7b` |
| 安全性の分類器 | `cais/HarmBench-Llama-2-13b-cls`, `allenai/wildguard`, StrongREJECT の `finetuned_gemma` |
| AlpacaEval の judge | `weighted_alpaca_eval_gpt4_turbo`（OpenAI API。鍵はルートの `.env`） |

SST-Merge の提案論文 SAGAI_EN_sst の実験は、別のベース（Llama-3.1-8B、`論文/SAGAI_EN_sst/main.tex` L784, L1064）と、その上の LoRA アダプタ（A5: RepliQA、A6: Alpaca、A7: Jailbreak Trigger）を使う。v3 の設定にはこれらのモデルは出てこない（`architecture.md` の対応表）。論文の数値を出した v1（リポジトリ外）のベースは `meta-llama/Llama-3.1-8B-Instruct` である（`v1/core/sst_merge.py` L42）。

### 外部モデルの系統（config.json で確認）

ローカルの HF キャッシュ（`~/.cache/huggingface/hub/models--*/snapshots/*/config.json`、リポジトリ外）の `config.json` だけを読んだ。重みは開いていない。

| モデル | `_name_or_path` | 系統の手がかり | vocab_size | 判定 |
|---|---|---|---|---|
| `meta-llama/Llama-2-7b-hf`（θ₀） | `meta-llama/Llama-2-7b-hf` | `max_position_embeddings: 4096`, `rms_norm_eps: 1e-05`, `rope_theta` 指定なし（既定 10000） | 32000 | ベース |
| `WizardLMTeam/WizardMath-7B-V1.0` | `/model_weights/` | `max_position_embeddings: 2048`, `rms_norm_eps: 1e-05`, `pad_token_id: 0` | 32001 | config からは判定できない（Llama-2-7B 系とされるが未検証） |
| `vanillaOVO/WizardCoder-Python-7B-V1.0` | `/workspaceblobstore/caxu/trained_models/7Bcodellamapython_v1_2048_e3_2e_5/checkpoint-195` | `rope_theta: 1000000`, `max_position_embeddings: 16384` | 32001 | CodeLlama-Python-7B 系。Llama-2-7b-hf からの直接の FT ではない |
| `medalpaca/medalpaca-7b` | `../llama-7b-hf/` | `rms_norm_eps: 1e-06`, `max_sequence_length: 2048`, `transformers_version: 4.28.0.dev0`, `torch_dtype: float32` | 32001 | LLaMA-1 7B 系。Llama-2 系ではない |

影響は `code-quality-assessment.md` の仮説 (d) を参照。merge 済みモデルはベースの config で保存される（`scripts/merge.py` L622-633）。

## 開発ツール

- Linter / Formatter: なし
- テスト: `unittest`（`scripts/tests/test_steering_hook.py`）、自作の統合スクリプト（`scripts/tests/test_merge_all.py`）
- CI: なし

## リポジトリ外（v1 / v2）のスタック（読んだ範囲）

| 項目 | v1 | v2 |
|---|---|---|
| ベースモデル | `meta-llama/Llama-3.1-8B-Instruct`（`core/sst_merge.py` L42、FT スクリプト、全ドライバ） | `configs/aaai27/llama2_sst_experiment.yaml` は `meta-llama/Llama-2-7b-hf` と WizardMath / WizardCoder / medalpaca。`config_example.yaml` は Llama-3.1-8B-Instruct。README と FT の既定は Meta-Llama-3-8B-Instruct |
| 学習済みアダプター | A5 = RepliQA、A6 = Alpaca、A7 = Safety。LoRA r=16、alpha=32、dropout 0.05、7 種の proj、lr 2e-4、A5 / A6 は 10 epoch、バッチ 2（`scripts/FT/*_tune.py`） | `run_lora_ft.py`（r=16、7 種の proj）で Utility / Safety / Mixed / Coding |
| 主なライブラリ（`requirements.txt`） | torch>=2.0.0, transformers>=4.30.0, peft>=0.4.0, accelerate>=0.20.0, bitsandbytes>=0.41.0, datasets>=2.12.0, evaluate>=0.4.0, scikit-learn>=1.3.0, hydra-core>=1.3.0, pytest>=7.3.0 ほか。`rouge_score` と分類器（`LibrAI/longformer-harmful-ro`）は評価スクリプトが使う | torch>=2.0.0, transformers>=4.40.0, peft>=0.10.0, trl>=0.8.0, accelerate>=0.29.0, xformers>=0.0.25, fschat>=0.2.36, openai>=1.14.0, datasets>=2.16.0 ほか。mergekit と lm-evaluation-harness は `scripts/setup_env.sh` で取得 |
| 仮想環境 | ワークスペースの `venv_sst`（`run_all_experiments.sh` L26-30） | 同上（未確認） |
| 数値精度 | モデルは fp16（`sst_merge.py`）または bf16（ドライバの FIM とアダプターのフル化） | ストリーミング merge は元のテンソルの dtype、mergekit は `float16` |
| 評価 | JB: TrustLLM の longformer 分類器（500 プロンプト、greedy 256 トークン）。有用性: ROUGE-1（`rouge_score`、stemmer あり） | 4 ベンチ + lm-eval（config）、FT ベースラインは ID / OOD の評価 |
