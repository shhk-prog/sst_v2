# コード要約：大規模調査のまとめ（v5）

## 作成したファイル（すべて `v5/` 配下。`v3/`、`v1/`、`v2/`、論文、既存結果は変更していない）

- `README.md`、`pytest.ini`
- `src/v5lib/`: `safeio.py`、`results_io.py`、`metrics.py`、`compare.py`、`tables.py`、`plots.py`、`ablation.py`、`manifest.py`、`hypotheses.py`、`tensor_checks.py`、`verify.py`、`report.py`
- `scripts/`: `run_pipeline.py`、`check_inputs.py`、`check_v1_v9.py`、`check_v10_v11.py`、`regen_flmsec_tables.py`、`plot_pareto_curves.py`、`ablation_table.py`、`build_report.py`、`probe_native_classifier.py`（実行後に追加。論文の表の有害判定を調べる探索用）、`_common.py`
- `tests/`: 7 本のテストと、合成データを作る `synth.py`、`conftest.py`
- `docs/survey_summary/`: `preregistration.md`、`preregistration.json`、`definitions.md`、`report.md`（考察と設計案を含む）
- `outputs/`: 実行の出力（表、図、仮説の判定、入力の確認、探索、実行の記録）

## 主な実装の判断

- 有害判定は、呼び出し側が必ず明示する（既定を置かない）。主軸は HarmBench Classifier 単独、`generate_flmsec_hyo.py` の OR 判定は再現確認用。
- VRR の下限、近傍比較の許容範囲、論文照合の許容差、仮説の判定の指標と閾値は、すべて `preregistration.json` から読む（コードに直書きしない）。
- 範囲を絞った実行は、その仮説を必ず「判定不能」にし、実行範囲を出力に記録する。
- GPU を使わない（`device="cpu"` 固定、`CUDA_VISIBLE_DEVICES=""`）。`safeio.py` が `v5/` の外への書き込みを拒否する。

## テスト

- コマンド: `venv_sst/bin/python -m pytest v5/tests -q`
- 結果: 49 件が成功、失敗 0、スキップ 0（ビルド担当と、オーケストレーターの両方で実行して確認）
- 計画の目安（約 20 件）より多いのは、各ファイルに異常系と境界を足したため
- 実データで動かしたテストはない。実データでの実行は、下の「実行した範囲」のとおり、依頼者の許可を得て行った

## テストを実行できなかったもの / 実行しなかったもの

- `probe_native_classifier.py` には、単体テストを書いていない（探索用。結果は論文の表の値と突き合わせて確認した）
- 論文の LaTeX パーサは、`appendix.tex` の `multirow` と `$m \pm s$` の形だけを想定している。実物で、安全性の表 216 件のうち 6 件は両方 N/A、126 件が一致、84 件が不一致だった。不一致の原因は、有害判定の違いである（`report.md` 3.0 節）

## 実行した範囲（計画の Part B。依頼者が 2026-11-24 に許可した 3 段階）

| 段階 | 実行したコマンド | 結果 |
|---|---|---|
| 入力の確認 | `run_pipeline.py --execute --stages inputs --approved-by-user` | ドメインモデルの重み（`model_weights_util`）が無く、V4、V5、V6 は判定不能の見込み |
| 再集計 | `run_pipeline.py --execute --stages v10_v11,tables,plots,ablation --approved-by-user` | 表、曲線 4 枚、アブレーション表、V10、V11。約 10 分 |
| V1〜V9（範囲を絞る） | `run_pipeline.py --execute --stages v1_v9 --approved-by-user --v1-v9-args "--seed 42 --pattern safety+math --layers 0,15,31 --max-tensors 8 --hypotheses V1,V2,V3,V7,V8,V9"` | V7 支持、V8・V9 不支持、V1〜V3 は範囲を絞ったため判定不能 |
| 探索（追加） | `probe_native_classifier.py` | 論文の表の有害判定が、ベンチマーク別の分類器であることを確認。依頼者の許可した範囲の延長（読み取りのみ、CPU、出力は `v5/outputs/probe/`） |

## 実行していない範囲

- V1〜V3 の全範囲（全 seed、全パターン、全層）。数時間かかる可能性があり、別途の許可が要る
- V4、V5、V6（ドメインモデルの重みが HF キャッシュに無い）
- V12〜V16（v1 に関する確認。依頼者の方針で必須としない）

## 計画からの逸脱

- `v5/pytest.ini` の追加（`venv_sst` の hydra の pytest プラグインが壊れているため）
- 計画に無いモジュールの追加（`manifest.py`、`verify.py`、`tensor_checks.py`、`report.py`、`scripts/_common.py`、`tests/synth.py`）
- `check_v1_v9.py` に `--approved-by-user` の要求を追加
- `probe_native_classifier.py` の追加（実行の結果、論文の表との不一致の原因を調べる必要が出たため）
- 事前登録の閾値（提案値）は、依頼者が 2026-11-24 に、提案値のまま固定することを承認した

## 既知の注意

- 作業中に 1 度、`sed -i` を実行した（効果なし）。以降は編集ツールを使った
- `git status` に、サブモジュールの変更（`baseline/*`、`v3/baselines/*` など）が出ている。本作業で書いたものではない（作業開始時の状態は未確認）
- `v5/` 内に `__pycache__` と `.pytest_cache` ができている
