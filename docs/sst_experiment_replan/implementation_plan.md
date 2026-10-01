# SST-Merge 実験再計画：学習データセットと評価体系の定義

指示追従能力と専門性を両立させ、トップ会議（NeurIPS/ICML等）の基準に耐えうる厳密な評価を行うため、学習データセットおよび評価体系を以下の通り定義・変更しました。

## 1. 学習データセット (Fine-Tuning Data)

特定のドメイン知識と安全性をバランスよく学習させるため、以下の3カテゴリで構成します。

| カテゴリ | データセット | 件数 | 内容・目的 | 根拠・参考文献 |
| :--- | :--- | :--- | :--- | :--- |
| **Finance** | `gbharti/finance-alpaca` | 4,500件 | 推論・QAを含む対話形式の金融指示データ | [Taori et al. (2023)](https://crfm.stanford.edu/2023/03/13/alpaca.html) (Alpaca手法の適用) |
| **Coding** | `Magicoder-OSS-Instruct-75K` | 4,500件 | OSSコードを基にした高品質な指示データ | [Wei et al. (2024)](https://arxiv.org/abs/2312.02120) (OSS-Instruct) |
| **Safety** | `AdvBench` + `TrustLLM` | ~2,000件 | 脱獄攻撃への拒絶応答および信頼性向上 | [Zou et al. (2023)](https://arxiv.org/abs/2307.15043) / [Huang et al. (2024)](https://arxiv.org/abs/2401.05561) |

## 2. 評価体系 (ID/OOD Evaluation Framework)

モデルの「ドメイン知識の定着度 (In-Domain)」と「汎化性能・忘却耐性 (Out-Of-Domain)」を切り分けて評価します。

| カテゴリ | 評価タイプ | データセット / ベンチマーク | 指標 | 根拠・参考文献 |
| :--- | :--- | :--- | :--- | :--- |
| **Safety** | **ID** (学習済み) | AdvBench + TrustLLM | ASR ↓ | [Zou et al. (2023)](https://arxiv.org/abs/2307.15043) / [Huang et al. (2024)](https://arxiv.org/abs/2401.05561) |
| | **OOD** (未知) | **HarmBench** | ASR ↓ | [Mazeika et al. (2024)](https://arxiv.org/abs/2402.04249) |
| | **Over-refusal** | **XSTest** | FPR ↓ | [Röttger et al. (2024)](https://arxiv.org/abs/2308.01263) |
| **Finance** | **ID** (学習済み) | finance-alpaca (eval split) | ROUGE-L | - |
| | **OOD** (未知) | **MMLU** (Biz-Ethics, Macro, Econ) | Accuracy | [Hendrycks et al. (2021)](https://arxiv.org/abs/2009.03300) |
| **Coding** | **ID** (学習済み) | Magicoder (eval split) | ROUGE-L | [Wei et al. (2024)](https://arxiv.org/abs/2312.02120) |
| | **OOD** (未知) | **HumanEval**, **MBPP**, **GSM8K** | pass@1 / EM | [Chen et al. (2021)](https://arxiv.org/abs/2107.03374) / [Austin et al. (2021)](https://arxiv.org/abs/2108.07732) / [Cobbe et al. (2021)](https://arxiv.org/abs/2110.14168) |
| **General** | **OOD** (汎用) | **ARC-C**, **HellaSwag** | Acc_norm | [Clark et al. (2018)](https://arxiv.org/abs/1803.05457) / [Zellers et al. (2019)](https://arxiv.org/abs/1905.07830) |

---

## 3. 実装計画 (Proposed Changes)

### [MODIFY] `v2/scripts/fine_tuning/run_phase2.sh`
*   **データセット構成の変更**: 上記の件数（Finance 4.5k, Coding 4.5k, Safety 2k）に合わせ、トレーニングスクリプトのデータサンプリング引数を更新します。
*   **評価ループの追加**: 従来の `eval_type="general"` に加え、`mmlu_finance`, `humaneval` などの OOD 評価をフェーズ2の評価パイプラインに明示的に組み込みます。

### [NEW/MODIFY] 過剰拒絶・OOD安全性評価の実装
*   **XSTest/HarmBench の統合**: 
    `run_safety_eval.py` を拡張し、HarmBench (OOD攻撃) と XSTest (過剰拒絶) を同時に測定し、ASR (Attack Success Rate) と FPR (False Positive Rate) を算出可能にします。

### [MODIFY] `docs/sst_experiment_replan/task.md`
Phase 2（学習）および Phase 4（評価）の項目を、本計画の ID/OOD 構成に合わせて詳細化します。

---

## User Review Required (ユーザーへの確認事項)

> [!IMPORTANT]
> 1. **GSM8K の位置づけ**: GSM8K は算数文章題ですが、ここでは Coding (論理推論) の OOD 評価として配置しています。Coding FT の効果が波及しているかを測定する意図ですが、問題ないでしょうか？
> 2. **計算リソース**: ARC-C や HellaSwag の評価は時間がかかるため、中間チェックポイントではスキップし、最終モデル（またはマージ後）のみで実行する運用を想定しています。

## 参考文献 (References)

1.  **Alpaca**: Taori, R., et al. (2023). "Alpaca: A Strong, Replicable Instruction-Following Model." Stanford CRFM.
2.  **Magicoder**: Wei, Y., et al. (2024). "Magicoder: Empowering Code Generation with OSS-Instruct." ICML 2024.
3.  **AdvBench**: Zou, A., et al. (2023). "Universal and Transferable Adversarial Attacks on Aligned Language Models." arXiv:2307.15043.
4.  **TrustLLM**: Huang, Y., et al. (2024). "TrustLLM: Trustworthiness in Large Language Models." ICML 2024.
5.  **HarmBench**: Mazeika, M., et al. (2024). "HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal." ICML 2024.
6.  **XSTest**: Röttger, P., et al. (2024). "XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models." NAACL 2024.
7.  **MMLU**: Hendrycks, D., et al. (2021). "Measuring Massive Multitask Language Understanding." ICLR 2021.
8.  **HumanEval**: Chen, M., et al. (2021). "Evaluating Large Language Models Trained on Code." arXiv:2107.03374.
9.  **MBPP**: Austin, J., et al. (2021). "Program Synthesis with Large Language Models." arXiv:2108.07732.
10. **GSM8K**: Cobbe, K., et al. (2021). "Training Verifiers to Solve Math Word Problems." arXiv:2110.14168.
11. **ARC**: Clark, P., et al. (2018). "Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge." arXiv:1803.05457.
12. **HellaSwag**: Zellers, R., et al. (2019). "HellaSwag: Can a Machine Really Finish Your Sentence?" ACL 2019.
