# テスト結果：v5

実行日: 2026-11-24。実行場所: ワークスペース直下。

## ビルド

| コマンド | 終了コード | 結果 |
|---|---|---|
| `venv_sst/bin/python -m compileall -q v5/src v5/scripts v5/tests` | 0 | 成功（出力なし） |
| `venv_sst/bin/python v5/scripts/run_pipeline.py --dry-run` | 0 | 6 段階のコマンドを表示。何も書いていない |

## 単体テスト

コマンド（Code Generation の `unit-test-instructions.md` と同一。1 回だけ実行）:

```
venv_sst/bin/python -m pytest v5/tests -q
```

- 終了コード: 0
- 合計 49 件、成功 49、失敗 0、スキップ 0（12.11 秒）
- 失敗の詳細: なし

## カバレッジ

測りません。poc の方針で、行カバレッジの下限は無く、プロジェクト全体の下限を設定したものも無いため、全体のカバレッジ実行は行っていない。

## 統合・性能・セキュリティ

Minimal 戦略のため、これらの手順書は作っていない。実行もしていない。

## 実データの実行（Code Generation の Part B で実施済み）

依頼者が 2026-11-24 に許可した範囲を、Code Generation 段階で実行した。結果は `code-summary.md` にある（V7 支持、V8・V9 不支持、V1〜V3 は範囲を絞ったため判定不能、V4〜V6 はドメインモデルの重みが無く判定不能の見込み）。この段階では再実行していない。

## 保全の確認（NFR2）

`git status --short -- v3/results v1 v2` は、変更なし（出力が空）。

## Loop-Back Log

なし（失敗が無かったため、ループバックは起きていない）。
