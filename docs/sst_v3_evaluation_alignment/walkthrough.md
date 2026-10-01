# 修正内容の確認 (Walkthrough)

直接評価データセット（`Evol-Instruct-Code` および `MedAlpaca`）の評価統合を完了しました。

## 変更内容の概要

### 1. 専用評価スクリプトの作成: [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_instruction_datasets.py)
*   **データロード**: 
    `datasets` ライブラリを使い、`nickrosh/Evol-Instruct-Code-80k-v1` と `medalpaca/medical_meadow_medical_flashcards` を決定論的にロード。FIM訓練用に使用した先頭1000サンプルとの重複を避けるため、**インデックス1000以降からサンプルを抽出**。
*   **メトリクス計算**:
    *   **Perplexity**: 正解出力テキストに対するトークンレベル損失値を計測。
    *   **Similarity Score**: モデルにテキスト生成を行わせ、正解ターゲット文字列との編集距離類似度（Sequence Similarity Ratio）を測定。

### 2. 実験スクリプトの拡張: [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
*   ベースモデル評価時およびすべてのマージモデル（`ties`, `diagonal_sst`, `della` 等）の評価時に、今回追加した直接評価を実行するループを追加。
*   結果は lm-eval 評価ファイルや AlpacaEval 2 ファイルとは区別され、`{model_name}_inst_{dataset}.json` に保存されます。

### 3. パレート分析の対応: [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)
*   分析対象のユーティリティデータとして `{base_name}_inst_evol_code.json` と `{base_name}_inst_medalpaca.json` をロードするブロックを追加。
*   `similarity_score` を `utility` スコアとして読み込み、`utility_domain = "inst_evol_code"` / `"inst_medalpaca"` でDataFrameに統合されます。

## 検証結果
テスト実行のコマンドをターミナルで実行して動作を確認できます。
