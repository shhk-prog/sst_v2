# Utility ファインチューニング改善計画 (Phase 2: コーディング性能の向上)

## 現状の課題とこれまでの経緯

`coding_lora` の学習において、ベースモデルと比較してコーディング性能（HumanEval / MBPP）が大幅に向上しない問題に取り組んでいます。

### これまでに解決したこと (Phase 1)
1. **Template Mismatch の解消**: 評価時 (`run_utility_eval.py`) に `--apply_chat_template` を適用し、学習時と評価時のフォーマットを一致させました。
2. その結果、**GSM8K (数値推論) はベースモデル比 +11 pp** と明確な学習効果が確認されました。しかし、HumanEval と MBPP はベースモデルと同等でした。

### 今回判明した新たな課題
「学習データの `output` に含まれる自然言語の解説文が HumanEval 評価の早期終了条件 (`\ndef`) と干渉している」という仮説のもと、データから解説文を除去するクリーニングを実施して再学習を行いました。

**クリーニング結果 (`coding_lora_clean`)**:
- ❌ **HumanEval**: 26.8% → **14.6%** (大幅悪化、baseの28.7%からも大きく低下)
- △ **MBPP**: 46.2% → **46.4%** (横ばい)
- ✅ **GSM8K**: 26.2% → **29.9%** (さらに向上)

> [!WARNING]
> **結論**: 解説文を完全に削除するクリーニングは、Python 関数補完（HumanEval）においては**逆効果**でした。コードのみを出力させようとすると、補完タスクとしての振る舞いが崩れてしまう、または分布ギャップが広がってしまった可能性があります。

---

## 新たな仮説と今後のアプローチ (Phase 2)

HumanEval や MBPP のスコアをベースモデル以上に引き上げるため、以下の3つのアプローチを優先度順に提案・実施します。

### 1. 失敗した評価サンプルの分析 (Why did clean data fail?)
クリーニング版の HumanEval が 14.6% に落ちた直接の原因を特定します。
- `results/lm_eval_raw/coding_lora_clean/coding/.../samples_humaneval_*.jsonl` を確認し、モデルがどのような出力をした結果 Fail しているのか（Markdown ブロックが壊れているのか、別のタグが出ているのか、関数名が間違っているのか）を確認します。

### 2. 学習データのドメイン特化 (Python サブセット化)
Magicoder データセットには Java, C++, Swift など多様な言語が混在しています。一方、HumanEval / MBPP は Python 特化の評価です。
- Python に関連するデータのみをフィルタリングして学習させることで、分布ギャップを解消し、Python コーディング能力に特化させます。

### 3. 学習設定の再設計 (Loss と Early Stopping の見直し)
- **Early Stopping の回避**: 前回は `epoch 10` 指定にもかかわらず、`utility_coding_eval` による eval_loss の監視で `epoch 1.78` (step 500) 付近で早期終了していました。eval_loss の低下と HumanEval スコアが比例していない可能性があるため、Patience を増やすか Early Stopping を無効にして完走させます。
- **全文 Loss (`assistant_only_loss=False`) の検討**: Baseモデルに対しては、チャットの assistant 応答部分だけでなく、プロンプトを含めた全体の言語モデリングとして学習させた方が HumanEval (プレーンな補完) との相性が良い可能性があります。

---

## 提案する具体的なアクションプラン

> [!IMPORTANT]
> **ユーザーレビューをお願いします**
> 次のステップとして以下の順序で進める計画です。方針に問題がなければ承認をお願いします。

1. **ログ解析**: ターミナルから `coding_lora_clean` の HumanEval 評価ログ (`samples_humaneval_*.jsonl`) を抽出し、なぜ 14.6% に落ちたかの具体的な出力を分析する。
2. **スクリプト修正**: 
   - `prepare_datasets.py` を修正し、**Python コードを含むサンプルのみ**を抽出するロジックに変更（または追加）。クリーニング（解説文削除）は一旦**元の状態（解説文あり）**に戻すか、フェンス (` ```python `) だけを整える方針に緩和する。
   - `run_lora_ft.py` の Early Stopping の設定（`metric_for_best_model` 等）を見直す。
3. **再学習と再評価**: Python 特化のデータで再度 `coding_lora` を学習させ、スコアを比較する。



