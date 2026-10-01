# フェーズ2 実験データセットおよび評価仕様

本ドキュメントでは、フェーズ2の再設計に基づき使用される学習データセット、評価ベンチマーク、および評価手法の詳細についてまとめています。

---

## 1. 学習データセット (Fine-Tuning Data)

各LoRAモデルの学習には、指示追従（Instruction-Following）能力を維持しつつ専門性を高めるため、以下のデータセットを使用します。

| 分類 | データセット名 | サンプル数 (FT用) | 特徴・変更理由 |
| :--- | :--- | :---: | :--- |
| **Finance** | `gbharti/finance-alpaca` | 4,500 | 従来のセンチメント分類から、推論・QAを含む対話形式に変更。MMLU等の知識問題との転移学習効果を期待。 |
| **Coding** | `Magicoder-OSS-Instruct-75K` | 4,500 | OSSプロジェクトから抽出された高品質なコード指示データ。 |
| **Safety** | `AdvBench` + `TrustLLM` | ~1,000 | 脱獄プロンプト（Jailbreak）に対する拒絶応答（Refusal）を学習。 |

---

## 2. 評価体系 (Evaluation Framework)

学習に使用したデータ内での性能（ID: In-Distribution）と、未知のタスクに対する汎化性能（OOD: Out-of-Distribution）の両面から評価を行います。

### 2-1. Safety (安全性) 評価

| 区分 | ベンチマーク | 指標 | 判定手法 | 目的 |
| :--- | :--- | :---: | :--- | :--- |
| **ID** | `AdvBench` + `TrustLLM` | ASR ↓ | Llama-Guard-3-8B | 学習した拒絶パターンの定着度を確認。 |
| **OOD** | `HarmBench` | ASR ↓ | Llama-Guard-3-8B | 未知の攻撃に対する汎用的な安全性を確認。 |
| **OOD** | `XSTest` | FPR ↓ | Keyword + Llama-3 Judge | 安全なプロンプトを誤って拒否する「過剰拒否」を測定。 |

### 2-2. Utility (有用性) 評価

| 区分 | 分野 | ベンチマーク | 指標 | 目的 |
| :--- | :--- | :--- | :---: | :--- |
| **ID** | 金融 | `finance-alpaca` (eval split) | ROUGE-L | 学習データと同様のQAに対する正確性を確認。 |
| **OOD** | 金融 | `MMLU` (Biz-Ethics, Macro, Econ) | Accuracy | 金融・経済の専門知識の汎化性能を評価。 |
| **ID** | コード | `Magicoder` (eval split) | ROUGE-L | 学習したコード生成能力の定着を確認。 |
| **OOD** | コード | `HumanEval`, `MBPP` | pass@1 | 未知のコーディング問題の解法能力を評価。 |
| **OOD** | 算数 | `GSM8K` | Exact Match | 数学的推論能力の維持を確認。 |
| **OOD** | 汎用 | `ARC-C`, `HellaSwag` | Acc_norm | LoRA適用による「壊滅的忘却」の有無を監視。 |

---

## 3. 評価メトリクス定義

- **ASR (Attack Success Rate)**:
    - 攻撃成功率。判定モデル（Llama-Guard-3）が「Unsafe（有害）」と判定した応答の割合。低いほど安全。
- **FPR (False Positive Rate)**:
    - 偽陽性率（過剰拒否率）。XSTestの安全なプロンプトに対し、モデルが拒絶応答を返した割合。低いほど実用的。
- **ROUGE-L**:
    - ID評価で使用。正解文（Reference）とモデル出力の最長共通部分列（LCS）に基づくF1スコア。
- **pass@1**:
    - コード評価用。生成されたコードがテストケースをパスする確率。
- **Acc_norm**:
    - 多肢選択問題において、選択肢の長さによるバイアスを補正した正解率。

---

## 4. 判定モデルの仕様

- **安全性判定 (ASR)**:
    - `meta-llama/Llama-Guard-3-8B` を使用。Metaが公式に提供する安全性分類器。
- **過剰拒否判定 (FPR)**:
    - キーワードマッチングによる一次判定の後、`Llama-3-70B` 相当の Judge LLM を用いて、それが「安全な意図に対する正当な回答」か「過剰な拒否」かを最終判定。
