# v3/scripts の整理 タスク管理

## 概要
`v3/scripts` ディレクトリ内にある38個のスクリプト群を分類・整理し、不要ファイルの削除、機能ごとのディレクトリ構造化、呼び出しパスの更新および動作検証を行う。

## タスクリスト

- [x] 1. 現状のスクリプト群の調査と分類
  - [x] `v3/scripts` 内のファイル・ディレクトリ一覧の抽出
  - [x] 各スクリプトの役割・依存関係の特定
- [x] 2. 計画策定 (Implementation Plan の作成)
  - [x] `docs/organize_v3_scripts/implementation_plan.md` の作成
  - [x] ユーザーへの計画提示と承認獲得
- [x] 3. 整理の実行
  - [x] 不要ファイル（macOS隠しファイルなど）の整理
  - [x] ディレクトリ構造の作成 (`eval/`, `merging/`, `analysis/`, `tools/`, `tests/`, `fixes/`)
  - [x] スクリプトの適切なサブディレクトリへの移動
  - [x] 関連ファイル（`run_experiments.py`, `merge_eval_parallel.py`, `README.md`等）内の呼び出しパス更新
- [x] 4. 検証およびドキュメント作成
  - [x] 移動したスクリプトやパイプラインの構成確認
  - [x] `walkthrough.md` の作成と記録
