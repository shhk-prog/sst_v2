# Utility ファインチューニング性能低下の調査報告 (Walkthrough)

## 問題の経緯と根本原因

`utility_lora` (金融) および `coding_lora` (コード) のファインチューニング後の OOD 評価スコアがベースモデルと変わらなかった問題について、根本原因を特定し、評価パイプラインの修正を行いました。

### 判明した根本原因

1. **Template Mismatch（学習時と評価時のフォーマット不一致）**  
   - 学習時（`run_lora_ft.py`）: Baseモデル・Instructモデルを問わず、すべてのサンプルが **チャット形式**（`<|start_header_id|>user...<|eot_id|>` + `<|start_header_id|>assistant...`）に変換されて学習されていた。
   - 評価時（`run_utility_eval.py`）: `--apply_chat_template` が指定されておらず、評価プロンプトが **プレーンテキスト** のまま入力されていた。
   - 結果: LoRA の重みが期待するフォーマットと全く異なる入力が来るため、学習した能力が全く発揮されなかった。

2. **Instructモデル特有のフォーマット干渉**  
   `Meta-Llama-3-8B-Instruct` に `--apply_chat_template` を適用すると、HumanEval 等の評価で「Here is the solution to the problem:\n\n```python\n」のような前置きを生成し、評価スクリプトの途中終了条件（`\ndef`）に引っかかって 0% になるという別の問題が発生した。

---

## 実施した修正

1. **`run_utility_eval.py`**: `--apply_chat_template` フラグを追加し、LoRAアダプターのtokenizerを参照する `tokenizer={adapter_path}` を model_args に含めるよう修正。
2. **`run_phase2.sh`**: Finance/Coding/General の3つの OOD 評価ループにて、LoRAモデルには `--apply_chat_template` を自動付与し、`base_model` は従来通りプレーンテキスト評価を継続するよう修正。

---

## 本番評価結果（limit なし、フルデータセット）

**設定**: `Meta-Llama-3-8B` (Base) + `coding_lora` / チャットテンプレート適用あり

| Task | サンプル数 | coding_lora + template | base + template | 差分 |
|------|-----------|------------------------|-----------------|------|
| **HumanEval** (pass@1) | 164 | 26.8% ± 3.5% | **28.7% ± 3.5%** | −1.9 pp |
| **MBPP** (pass_at_1, 3-shot) | 500 | 46.2% ± 2.2% | **46.8% ± 2.2%** | −0.6 pp |
| **GSM8K** (exact_match, flexible) | 1,319 | **26.2% ± 1.2%** | 15.2% ± 1.0% | **+11.0 pp** |
| **Macro 平均** | — | **33.1%** | **30.2%** | **+2.9 pp** |

### 解釈

- **GSM8K で +11.0 pp** という明確な改善が確認された。チャット形式で学習した GSM8K 系（CoT 推論）の能力が、テンプレート修正により正しく発揮されるようになったことを示す。
- **HumanEval / MBPP はほぼ横ばい**（差分は ±2 pp 以内で、誤差範囲内）。Template Mismatch は解消されたが、コーディング能力の向上は限定的だった。

---

## 残る課題と今後の改善方針

HumanEval / MBPP での改善が見られなかった原因として、以下が考えられます。

### 原因1: 学習データ (`utility_coding.json`) の `output` に説明文が混入

確認したところ、`utility_coding.json` の `output` フィールドが以下のような形式になっている：
```
"```java\npublic class DriveTrainDescription {...}\n```\n\nThis solution provides a `DriveTrainDescription` class..."
```
コードブロックの後に「This solution provides...」という英語の解説が付いており、モデルがこのフォーマットを学習してしまっている。HumanEval の評価は `\ndef` が出た時点で生成を終了するため、解説文の中で `def` が出てしまうと不正な位置で打ち切られるリスクがある。

**→ 対応: `output` からコードブロックのみを抽出してクリーニングする**

### 原因2: Baseモデルとチャット形式学習の相性

`Meta-Llama-3-8B` (Base) は、そもそも「チャット形式で質問に答える」ことを RLHF 等で学習しておらず、チャットテンプレートで学習させてもその構造を十分に活用できない可能性がある。

**→ 対応: `assistant_only_loss=False`（全文Loss）で学習し直す、またはInstructモデルを使用する**

### 原因3: HumanEval / Magicoder の分布ギャップ

Magicoder (`utility_coding.json`) は Java, Python, Swift 等の多様な言語・タスクを含むが、HumanEval は Python の関数補完に特化している。学習分布と評価分布のミスマッチが残っている可能性がある。

---

## データクリーニングによる改善検証 (Phase 2)

上記の「原因1 (解説文の混入)」に対処するため、学習データ (`utility_coding.json`) から解説文を完全に除去（コードブロックの中身だけを抽出）するスクリプトを作成し、クリーンなデータで再度 `coding_lora_clean` を学習させました。

### クリーニング後の評価結果

| Task | base + template | coding_lora（未クリーン） | **coding_lora_clean** | 影響 (対 未クリーン) |
|------|-----------------|---------------------------|------------------------|---------------------|
| **HumanEval** | **28.7%** | 26.8% | **14.6%** | **−12.2 pp** (悪化) |
| **MBPP** | **46.8%** | 46.2% | 46.4% | ±0 (横ばい) |
| **GSM8K** (flexible) | 15.2% | 26.2% | **29.9%** | **+3.7 pp** (向上) |
| **Macro 平均** | 30.2% | **33.1%** | 30.3% | −2.8 pp |

### 結論と新たな考察

> [!WARNING]
> **結論: 解説文の完全除去は、コーディング（HumanEval）においては逆効果でした。**

- **HumanEval の大幅悪化**:
  解説文を除去したことで、モデルが「コードだけを無愛想に出力する」ようになったものの、HumanEval における関数補完（`def ...` に続くコードの生成）タスクにおいては、何らかの理由で分布がさらに悪化したと考えられます。
- **GSM8K のさらなる向上**:
  一方で、GSM8K ではスコアが伸びています。データクリーニングにより不要なノイズが減り、数学推論のようなタスクには良い影響を与えた可能性があります。

## 次のステップへの提案

データクリーニングだけでは HumanEval / MBPP が改善しない（むしろ悪化する）ことが分かったため、次は以下のアプローチを提案します。

1. **ログ解析**: 14.6% に落ちた HumanEval の出力ログを直接確認し、「何が出力されて失敗しているのか」を特定する。
2. **学習設定の再設計**: Early Stopping で学習が 1.78 epoch で早期終了しているため、これを完走させる。また、Base モデルに対して `assistant_only_loss=True` (応答のみの Loss) ではなく、全文 Loss で学習させる。
3. **データセットの Python 特化**: Magicoder データセットから Python 以外の言語をフィルタリングし、ドメインギャップを減らす。
