# 単体テストの実行手順：v5

## テストの枠組みと設定

- フレームワーク: pytest。ワークスペース直下の `venv_sst`（`sst_v2/venv_sst`）の Python で実行する
- 設定ファイル: `v5/pytest.ini` の 1 つだけ（壊れた hydra の pytest プラグインを止める。下の「環境の確認結果」を参照）。`v5/tests/` の下に `test_*.py` を置き、各ファイルの先頭で `sys.path` に `v5/src` を追加する（`v5/tests/conftest.py` に 1 か所だけ書く）
- 必要なパッケージ: pytest、numpy、matplotlib。`torch` と `safetensors` は検証層（`test_hypotheses.py`）が使う。足りないパッケージがあるときは、入れずに依頼者へ伝える（計画の Step 2.1）。`torch` が無い環境では、`test_hypotheses.py` の `torch` を使うテスト（g）は `pytest.importorskip("torch")` でスキップし、スキップした件数と理由を `code-summary.md` に書く

## 環境の確認結果（計画の Step 2.1、2026-11-23 に確認）

`venv_sst/bin/python` で確認した。足りないパッケージはない（何も入れていない）。

| パッケージ | 結果 |
|---|---|
| pytest | 9.0.3（使える） |
| numpy | 2.4.6（使える） |
| matplotlib | 3.10.9（使える。`Agg` バックエンドで使う） |
| torch | 2.12.0+cu130（使える。CPU だけで使う） |
| safetensors | 0.7.0（使える） |

注意（逸脱）: `venv_sst` には、壊れた hydra の pytest プラグイン（`hydra_core 1.3.2` と `antlr4` のバージョン不一致）が
入っており、`python -m pytest` が、プラグインの読み込みで失敗する（`Could not deserialize ATN with version`）。
v5 のテストは hydra を使わないので、`v5/pytest.ini` の `addopts = -p no:hydra_pytest` で、このプラグインだけを止める。
このため「設定ファイルは置かない」という当初の方針から外れ、`v5/pytest.ini` を 1 つ置いている。
`venv_sst` 自体は変更していない。

## このスコープのテストの実行コマンド

実行場所は、ワークスペース直下（`/mnt/nas/home/hiromi/src/sst_v2`）。コマンドは `v5/tests` だけを対象にする（プロジェクト全体の実行はしない）。

```
venv_sst/bin/python -m pytest v5/tests -q
```

ファイルごとの実行（層ごとに、実装の直後に実行する）:

```
venv_sst/bin/python -m pytest v5/tests/test_results_io.py -q
venv_sst/bin/python -m pytest v5/tests/test_metrics.py -q
venv_sst/bin/python -m pytest v5/tests/test_compare.py -q
venv_sst/bin/python -m pytest v5/tests/test_outputs.py -q
venv_sst/bin/python -m pytest v5/tests/test_hypotheses.py -q
venv_sst/bin/python -m pytest v5/tests/test_pipeline.py -q
venv_sst/bin/python -m pytest v5/tests/test_report.py -q
```

テストは、一時フォルダ（`tmp_path`）に作った合成の結果ファイルと、小さな合成のテンソルだけを使う。`v3/results/vllm`、`v3/cache`、`v3/models` の実データは開かない。GPU も使わない。

## テストの規模（Minimal）

要件ごとに 1 件以上、各コンポーネントに正常系 1 件を置く。計画の目安は約 20 件だったが、正常系に加えて異常系・境界を
各ファイルに足したため、実際は 49 件（下の表の「実績」）。

| ファイル | 件数の目安 | 実績 | 確認する要件 |
|---|---|---|---|
| test_results_io.py | 4 | 6 | FR3.4、NFR2、NFR3 |
| test_metrics.py | 6 | 9 | FR1.3、FR1.4、FR3.1 |
| test_compare.py | 5 | 6 | FR1.2、FR1.5 |
| test_outputs.py | 5 | 6 | FR3.1、FR3.2、FR3.3、FR3.4、NFR1 |
| test_hypotheses.py | 8 | 13 | FR2.1、FR2.2、FR2.3、FR2.4、NFR4 |
| test_pipeline.py | 2 | 4 | FR2.4 |
| test_report.py | 3 | 5 | FR6.1、NFR3 |

## 期待するカバレッジ

行カバレッジの下限は設けない（poc は、選んだテスト戦略 Minimal 以外の新しいテストの下限を足さない）。カバレッジの数値は報告しない。既存のテスト（`v3/scripts/tests/`）は変更しない。

## モック、スタブの指針

- ファイルの入出力は、`tmp_path` に合成のファイルを作って使う（ファイルシステムのモックはしない）
- 分類器、モデル、GPU は呼ばない。`is_gibberish` と `harmbench_cls_output` は、合成の JSON に直接書く
- 乱数を使う場合は seed を固定する

## テストデータの管理

- 合成データは、各テストファイルの中の関数（フィクスチャ）で作る。ファイルとしてリポジトリに置かない
- 安全性 JSON の合成データは、`results[]` に `is_gibberish`、`harmbench_cls_output`、`asr` を持つ最小の形にする（`api-documentation.md` の「安全性 JSON のスキーマ」）
- テンソルは、数十要素の `float32` にし、fp16 で 0 に落ちる値（1e-9 など）を含める

## テストを実行できないもの（`code-summary.md` に理由を書く）

- 実データ（`v3/cache/fim/*.pt`、`v3/models/`、`v3/results/vllm`）に対する実行は、単体テストでは行わない。依頼者の許可を得て、計画の Part B で実行する
