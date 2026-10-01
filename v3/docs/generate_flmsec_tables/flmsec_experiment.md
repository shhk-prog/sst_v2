# 予備実験およびメイン実験の実験設計書

本ドキュメントは、安全なモデルマージに関する予備実験およびメイン実験の設計（対象モデル、データセット、評価指標、マージ手法等）をまとめたものです。

## 1. 全体設定
- **ベースモデル (Base Model)**: `meta-llama/Llama-2-7b-hf`
- **対象ドメイン・モデル (Domain Models)**:
  - Math: `WizardLMTeam/WizardMath-7B-V1.0`
  - Code: `vanillaOVO/WizardCoder-Python-7B-V1.0`
  - Medical: `medalpaca/medalpaca-7b`
- **Safety モデル**: 独自データ (`data/response_dataframe.csv`) で Fine-Tuning した LoRA アダプタを使用。
- **乱数シード**: `42`, `43`, `44` の3パターンを用い、結果の頑健性（Mean ± Std）を検証。

---

## 2. 予備実験 (Preliminary Experiments)

### 目的
既存の安全性・有用性ベンチマーク（TrustLLM, BeaverTails）を用いた、各マージ手法のベースライン性能と安全性のトレードオフの確認。

### 評価内容
- **評価データセット**: `PKU-Alignment/BeaverTails` (`30k_test` スプリット) を有害・無害プロンプトに分割して利用。
- **データ数**: 有害プロンプト 500件、無害プロンプト 500件 (デフォルト設定)。
- **評価軸**:
  - **TrustLLM Raw ASR (ASR↓ %)**: 攻撃成功率。低いほど安全。
  - **Gibberish Ratio (崩壊率↑ %)**: 文字化けや繰り返しなど、推論の破綻率。高いとモデルが崩壊している。
  - **BeaverTails Utility (Score↑ %)**: 無害なプロンプトに対する適切な回答率 (Accuracy)。
- **評価の方法**: `LibrAI/longformer-harmful-ro` (テキスト分類モデル) を用いた自動分類（LABEL_1 を有害、LABEL_0 を安全と判定）。
- **マージ手法 (Merge Methods)**: 
  - `diagonal_sst`, `data_free_sst` (提案手法)
  - `task_arithmetic`, `ties`, `dare`, `della` (公式 mergekit ベースライン)
  - `matena_fisher`, `mergealign`, `safemerge`, `led_merging` (外部比較手法)
  - α(ハイパーパラメータ)の指定が可能なものはターゲットとするα(例: 0.6)を使用。

---

## 3. メイン実験 (Main Experiments)

### 目的
より広範かつ最新のドメイン固有ベンチマークと安全評価ベンチマークを用いて、各マージ手法（特にSST-Merge系）の効果と頑健性を詳細に評価。

### 評価内容
- **評価データセットと評価軸**:
  - **Safety**: `HarmBench`, `JailbreakBench`, `StrongReject`, `WildJailbreak`
    - 指標: 有害コンテンツ生成率 (ASR↓ %)。低いほど安全。
  - **Utility (Math)**: `GSM8K`, `Minerva Math500`
    - 指標: 正答率、Exact Match (%)
  - **Utility (Code)**: `HumanEval`, `MBPP`
    - 指標: Pass@1 (%)
  - **Utility (Medical)**: `PubMedQA`, `MedQA_4options`
    - 指標: 正答率 (%)
  - **Utility (General/Inst)**: `MMLU`, `IFEval`, `AlpacaEval 2`
    - 指標: 正答率、Length-controlled Win Rate 等 (%)
- **データ数**: 
  - 各ベンチマークの仕様に従う。
  - 本集計では `debug_limit320`（各タスク最大320件の制約下での評価結果）を利用して集計する。
- **評価の方法**: 
  - `lm-evaluation-harness` 経由での自動評価（正確な文字列マッチング等）。
  - LLM-as-a-Judge（GPT-4等）を利用した AlpacaEval の評価。
- **マージ手法と α スイープ**:
  - 予備実験と同様の手法を比較。
  - `alpha_sweep`: `0.0`, `0.2`, `0.4`, `0.6`, `0.8`, `1.0` を用いて、α値による Safety と Utility の変動（平均と平均以外の推移）を計測。
  - ベースモデル（マージ前）の性能も同様に評価・比較。

## 4. 集計データソース
テーブルの生成にあたっては、以下の2つのディレクトリ結果を照合します。
1. `/mnt/nas/home/hiromi/src/sst_v2/v3/results/vllm/debug_limit320`
2. `/mnt/nas/home/hiromi/src/sst_v2/v3/results/normal/debug_limit320`
両者の結果 (`normal` / `vllm`) を区別して出力し、性能差の有無を確認できるようにします。
