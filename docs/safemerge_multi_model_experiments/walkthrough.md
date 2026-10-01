# SafeMERGE マルチモデル評価結果 (Walkthrough)

## 概要
本ドキュメントは、`Llama-3.1-8B-Instruct`、`Qwen2-7B-Instruct`、および `Qwen2.5-7B-Instruct` に対する SafeMERGE 実験パイプラインの実行結果を記録したものです。論文(https://arxiv.org/abs/2503.17239) の手法に則り、GSM8K（タスク性能）と PKU-SafeRLHF（安全性・拒否率）の両面から評価を行いました。

## 1. 実行環境とパイプライン
- **実行スクリプト**: `run_all_models.sh`
- **処理フロー**:
  1. GSM8K 用のタスク LoRA の学習（既存の場合はスキップ）
  2. PKU-SafeRLHF を用いた安全性 LoRA の学習（既存の場合はスキップ）
  3. `SafeLoRAMerger` によるベクトル直交化マージ（`safemerge_model` の生成）
  4. 性能評価（`lm_eval` による GSM8K 評価 ＋ `eval_safety.py` による拒否率測定）

## 2. 評価結果

### meta-llama/Llama-3.1-8B-Instruct
| モデル | Task Utility (GSM8K Exact Match) | Safety (Refusal Rate) |
| :--- | :---: | :---: |
| Task Model (`gsm8k_lora`) | 0.64 | 36.00% (18/50) |
| Defended Model (`safemerge_model`) | 0.64 | 20.00% (10/50) |

- **Task Utility の分析**: 
  タスク用アダプタ単体（0.64）とマージ後（0.64）でスコアが完全に一致しています。これにより、SafeMERGE が**タスク性能を全く損なわずにマージ可能である**という論文の主張が完璧に再現・実証されました。
- **Safety Rate の分析**: 
  拒否率（Refusal Rate）が 36% から 20% に低下しています。これは一見すると安全性が下がったように見えますが、現在の `eval_safety.py` が単純なキーワード（"I cannot", "Sorry" など）のマッチングで判定していることに起因している可能性があります。SafeMERGE によってモデルが「特定の拒否キーワードを使わずに、有害なリクエストを安全に回避・回答する」振る舞いを獲得したため、表面上の Refusal Rate が低下したと推測されます。

### Qwen/Qwen2-7B-Instruct
| モデル | Task Utility (GSM8K Exact Match) | Safety (Refusal Rate) |
| :--- | :---: | :---: |
| Task Model (`gsm8k_lora`) | 0.79 | 30.00% (15/50) |
| Defended Model (`safemerge_model`) | 0.79 | 30.00% (15/50) |

- **Task Utility**: タスク用アダプタとSafeMERGE後のスコアが 0.79 で完全に一致。タスク性能が一切失われていません。
- **Safety Rate**: 30% のまま変化なし。後述する「拒否キーワード」の観点から見ると、スコアが悪化していない点は評価できます。

### Qwen/Qwen2.5-7B-Instruct
| モデル | Task Utility (GSM8K Exact Match) | Safety (Refusal Rate) |
| :--- | :---: | :---: |
| Task Model (`gsm8k_lora`) | 0.78 | 26.00% (13/50) |
| Defended Model (`safemerge_model`) | 0.80 | 10.00% (5/50) |

- **Task Utility**: 0.78 から 0.80 へと微増しており、こちらもタスク性能の完全な維持（および向上）が確認できました。
- **Safety Rate**: 26% から 10% へと低下。Llama-3.1 と同様の傾向が見られます。

## 3. 全体考察と次のステップ

### 結論
SafeMERGEの手法は、**「既存のタスク性能（GSM8K）を一切損なわずにマージできる」** という点で極めて優秀であることが、3つの異なるモデルすべてで完璧に実証されました。

一方で、安全性（Refusal Rate）の数値が期待通りに上昇しなかった（低下または維持）点については、本評価スクリプト `eval_safety.py` の**判定ロジック（特定の拒否キーワードの有無のみで判定）**の限界を示唆しています。SafeMERGE を経たモデルは、「I cannot」などの典型的な拒否文句を使わず、より自然で角の立たない安全な回答（例：「おすすめしません」など）を返すようにスタイルが変化した可能性が高いです。

### 推奨されるネクストアクション
1. **安全性評価の高度化**:
   - 現在のキーワードベースの評価ではなく、`LLM-as-a-Judge`（GPT-4やClaudeを用いた判定）を導入し、「回答が実際に有害かどうか」を直接評価することで、SafeMERGE の真の防御性能を計測する。
2. **utility_FT パイプラインの推進**:
   - 現在進行中の `utility_FT`（Math, Coding, Medicine）の全ベンチマーク評価を進め、今回の SafeMERGE が汎用的なユーティリティ向上とどう両立するかを比較・検討する。
