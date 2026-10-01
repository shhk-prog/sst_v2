# フルスケール評価ベンチマーク 実行タスクリスト

- `[x]` 1. **A. lm-evaluation-harness の拡張**
  - 公式でサポートされている数学タスク、GLUE、医学タスクの確認
  - `run_eval_all_utility.sh` に組み込み（カスタム不要のもののみ）
- `[x]` 2. **B. コーディング評価の実装**
  - `bigcode-evaluation-harness` のセットアップ確認
  - `run_eval_coding.sh` の作成と `mbpp`, `humaneval` 実行パイプラインの構築
- `[x]` 3. **C. 通信・専門ドメイン (TeleQnA) の実装**
  - `TeleQnA` リポジトリの評価スクリプト調査
  - `run_eval_telecom.sh` の作成とパイプライン構築
- `[x]` 4. **D. Safety (安全性・アライメント) の実装**
  - 必要な公式リポジトリ (HarmBench等) の調査とクローン
  - `Llama-Guard-3-8B` 等を用いた評価スクリプト `run_eval_safety.sh` の構築
- `[x]` 5. **マスタースクリプトの統合**
  - `run_all_benchmarks.sh` を作成し、A〜Dすべてを一括で実行できる基盤を整備
