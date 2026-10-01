# 評価結果ディレクトリの pattern 別再編成 タスク管理

## 概要
`results/debug_limit320/merged/` (および関連結果出力) において、`seed` の配下にマージパターン (`safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`) の階層ディレクトリを追加し、既存結果の移動およびパイプライン側のパスロジック更新を行う。

## タスクリスト

- [x] 1. ディレクトリ構成の調査と移行スクリプトの作成
  - [x] 現状のファイル名・パターン名の特定
  - [x] 再編成用計画書 (`implementation_plan.md`) の作成
- [x] 2. 計画の提示と承認
  - [x] ユーザーに Implementation Plan を提示し承認を得る
- [x] 3. 整理とスクリプト更新の実行
  - [x] 既存ファイル・ディレクトリの移動スクリプト作成
  - [x] パイプラインスクリプト (`merge_eval_parallel.py`, `v3/README.md` 等) のパス生成ロジック更新
- [x] 4. 検証と報告
  - [x] 移動用コマンドの提示と動作確認
  - [x] `walkthrough.md` の作成と報告
