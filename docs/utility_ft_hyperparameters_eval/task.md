# タスクリスト

ハイパーパラメータ最適化後（学習率 2.0e-5）のフルパイプライン実行結果の集計タスク管理リスト。

- [x] フルパイプライン実行ログ (`logs/full_pipeline_optimized_hyperparameters.log`) の確認と解析
- [x] 各モデル (BaseModel, Math, Coding, Medicine) の各種スコア抽出
  - [x] lm-eval (GSM8K, Minerva Math, GLUE, PubMedQA)
  - [x] coding (MBPP)
  - [x] telecom (TeleQnA)
- [x] 評価結果比較表の作成
- [x] 傾向分析とまとめの作成
- [x] プロジェクト内 `docs/utility_ft_hyperparameters_eval/` へのドキュメント保存
- [x] ユーザーへの結果報告
