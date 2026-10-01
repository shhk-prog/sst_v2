# Implementation Plan: SafeMERGE 評価パイプラインの構築

## 目的
作成した SafeMERGE マージモデル（および比較用のベースモデルやタスク特化モデル）に対して、論文と同様の観点で「タスク性能（Utility）」と「安全性（Safety）」のトレードオフを定量的に評価する仕組みを実装する。

## 評価指標と手法

論文（arXiv:2503.17239）では、タスク性能にGSM8Kなどの正答率（Exact Match）、安全性にDirectHarmやHexPhiなどのベンチマークを用いた攻撃成功率（ASR）などを採用しています。これらをローカル環境で効率よく再現するため、以下の構成を提案します。

### 1. タスク性能評価 (GSM8K)
デファクトスタンダードである `lm-evaluation-harness` (EleutherAI) を用いて、GSM8K の Few-shot 性能（Exact Match）を測定します。
- **実装内容**: `lm-eval` コマンドラインツールを呼び出すラッパースクリプトを作成。
- **対象モデル**: 
  1. マージ前タスクモデル（`outputs/gsm8k_lora` 適用）
  2. マージ済みモデル（`outputs/safemerge_model` 適用）

### 2. 安全性評価 (Safety / Refusal Rate)
安全性を自動で測定するため、悪意のあるプロンプト（Adversarial Prompts / 危険な指示）を入力し、モデルが正しく「回答を拒否（Refusal）」できるかの割合を測定する簡易スクリプトを作成します。
- **実装内容**: `eval_safety.py` の作成。
- **データセット**: `PKU-SafeRLHF` のプロンプトセット、あるいは標準的な `AdvBench` などを利用して危険な指示を数十〜数百件抽出。
- **判定方法**: 生成されたテキストに "I cannot", "As an AI", "Sorry" などの拒否キーワードが含まれているかをチェックし、Safety Rate（安全率）を算出するヒューリスティック評価。

### 3. 評価実行用パイプライン
- **[NEW] `run_evaluation.sh`**
  上記2つの評価（タスク評価と安全性評価）を各モデルに対して一括で実行し、結果を `outputs/eval_results/` にまとめるシェルスクリプト。

## 確認事項 (User Review Required)
> [!IMPORTANT]
> 1. **GSM8Kの評価ツール**: 業界標準の `lm-eval` を利用するため、追加で `pip install lm-eval` が必要になりますがよろしいでしょうか？（独自で回答抽出スクリプトをゼロから書くより確実・正確です）。
> 2. **安全性のデータセット**: 論文と同じ DirectHarm を完全に再現するのはセットアップが重くなる可能性があるため、まずは軽量なキーワードベースの拒否判定（AdvBench等を利用）を実装する方針で進めてもよろしいでしょうか？（より厳密な評価が必要な場合は、Llama-GuardなどのLLM-as-a-Judgeモデルをロードして判定させることも可能です）。
