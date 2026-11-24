# ビルドとテストのまとめ：v5

## 全体の状態

- ビルド: 成功（構文確認と `--dry-run` が終了コード 0）
- 単体テスト: 49 件すべて成功（失敗 0、スキップ 0）
- 必要な前提: `venv_sst`（追加の導入なし）、ワークスペース直下から実行

## テストの種類

| 種類 | 作成 | 理由 |
|---|---|---|
| 単体テスト | Code Generation で作成済み（7 ファイル） | Minimal 戦略の中心 |
| 統合・性能・セキュリティ | 作らない | Minimal 戦略では手順書を作らない |

## カバレッジの見込み

下限なし（poc）。数値は測っていない。要件ごとに 1 件以上のテストがある（`unit-test-instructions.md` の表）。

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|---|---|---|---|---|---|---|
| NFR1 | requirements.md NFR1 | 同じ入力から同じ出力 | 同一出力を確認（`test_outputs.py` の再実行テスト） | `test-results.md` の単体テスト（49 件成功） | build-and-test | Met |
| NFR2 | requirements.md NFR2 | `v3/results/vllm` などの変更 0 件、書き込みは `v5/` のみ | 変更 0 件。`v5/` の外への書き込みは拒否 | `git status --short -- v3/results v1 v2` が空、`test_results_io.py` の `safe_write` テスト | build-and-test | Met |
| NFR3 | requirements.md NFR3 | 数値が元ファイルのパスまで辿れる | 数値の行に元ファイルのパスが付く | `test_report.py`（成功）、`cross-unit-traceability.md` | build-and-test | Met |
| NFR4 | requirements.md NFR4 | GPU を使わず CPU のみ | `device="cpu"` 固定、`pipeline` は許可なしの実行を拒否 | `test_hypotheses.py`、`test_pipeline.py`（成功） | build-and-test | Met |
| NFR5 | requirements.md NFR5 | README・レポート・コメントは日本語 | 日本語で記述 | `v5/README.md`、`v5/docs/survey_summary/` | build-and-test | Met |
| TC-existing-suite | code-generation-plan.md Testing Contract（poc の下限） | 既存のテストが緑のまま | v5 の 49 件が成功。既存の `v3/scripts/tests/` は変更していない | `test-results.md` | build-and-test | Met |
| TC-ci | code-generation-plan.md Testing Contract | CI での実行 | N/A：この計画は CI Pipeline を実行しない | `aidlc-state.md`（ci-pipeline は SKIP） | build-and-test | N/A |

## 準備の評価

- build-ready: はい
- test-ready: はい
- deployment-ready: 該当なし（デプロイする成果物は無い）

## 既知の制限と残る項目

- 実データの実行は V1〜V3 の全範囲、V4〜V6（ドメインモデルの重みが無い）、V12〜V16 を実行していない（`code-summary.md`）
- `probe_native_classifier.py` には単体テストが無い（探索用）
- `git status` に出るサブモジュールの変更は、本作業で書いたものではない（作業開始時の状態は未確認）
- NFR5 は目視の確認であり、自動テストは無い
