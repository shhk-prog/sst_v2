# v5: 大規模調査のまとめ

FLMSEC 論文に使った v3 の大規模調査の結果（`v3/results/vllm`）を再集計し、secure merge に適した要素を抜き出して、
DLSP_hiromi2 に組み込む新しい merge 手法の設計案の根拠をつくるためのフォルダである。
既存手法のランキングではなく、設計要素の抽出が目的である。新しい実験（GPU ジョブ）は行わない。

- 比較の方法と採用基準: `docs/survey_summary/preregistration.md`（実データの実行の前に固定。機械が読む値は同名の `.json`）
- 指標の定義: `docs/survey_summary/definitions.md`
- レポート: `docs/survey_summary/report.md`（結果の節は `scripts/build_report.py` が自動生成。考察と設計案は手書き）
- 要件と計画: `aidlc/spaces/default/intents/261123-survey-summary/`（`requirements.md`、`code-generation-plan.md`）

## 守ること

- **v3、v1、v2、論文、既存の結果、モデル、キャッシュには書かない**（NFR2）。入力は読み取り専用で開く。
  書き込み先は `v5/` の下に限る。`v5lib/safeio.py` が、`v5/` の外への書き込みを例外にする。
- **GPU を使わない**（NFR4）。モデルの推論、学習、merge は起動しない。検証は CPU 専用で、`device="cpu"` 固定、
  スクリプトは `CUDA_VISIBLE_DEVICES=""` を設定する。
- **実データを読む実行の前に、実行するコマンドを依頼者に示して許可を得る**（FR2.4）。
  `run_pipeline.py --execute` と `check_v1_v9.py` は、`--approved-by-user` が無いと実行しない。
- 結果ファイル（`results/`）は追記専用の記録として扱う。確認用の実行の出力は、`v5/outputs/` の下に出る。

## 実行場所と環境

ワークスペース直下（`/mnt/nas/home/hiromi/src/sst_v2`）から、`venv_sst` の Python で実行する。
パッケージは入れない（numpy、matplotlib、torch、safetensors、pytest が必要）。

```
venv_sst/bin/python v5/scripts/<スクリプト>.py ...
```

## フォルダの構成

| 場所 | 内容 |
|:---|:---|
| `src/v5lib/` | ライブラリ（下の表） |
| `scripts/` | 実行の入口（下の表） |
| `tests/` | 単体テスト（合成データだけを使う。実データは開かない） |
| `docs/survey_summary/` | 事前登録、定義、レポート |
| `outputs/` | 生成した表、図、manifest、仮説の判定、実行の記録（実行すると作られる） |
| `pytest.ini` | `venv_sst` の壊れた hydra の pytest プラグインを止める設定 |

### ライブラリ（`src/v5lib/`）

| モジュール | 役割 |
|:---|:---|
| `safeio.py` | 読み取り専用の入力、`v5/` の下に限った書き込み |
| `results_io.py` | 結果ファイル名の解析、新旧の有用性ファイルの選択、目録（欠損、設定値、入力パス） |
| `metrics.py` | VRR、Conditional ASR、VSR、ベンチマーク ASR、有用性の集計。有害判定は呼び出し側が明示する |
| `compare.py` | VRR の下限でのふるい分け、厳密な Pareto 支配、近傍比較 |
| `tables.py` | 表の生成、FLMSEC 論文の表との照合 |
| `plots.py` | safety-utility 曲線（4 パターン各 1 枚） |
| `ablation.py` | SST のアブレーション表（k x variant）。欠損は N/A |
| `manifest.py` | 出力ごとの manifest（入力パス、件数、欠損、設定値） |
| `hypotheses.py` | 仮説 V1〜V11 の判定ロジック（事前登録の値を読む） |
| `tensor_checks.py`、`verify.py` | V1〜V9 のテンソル計算と実行部分（CPU、テンソルを 1 つずつ読む） |
| `report.py` | レポートの結果の節の組み立て |

### スクリプト（`scripts/`）

| スクリプト | 役割 | 出力先 |
|:---|:---|:---|
| `run_pipeline.py` | 段階ごとのコマンドの表示（`--dry-run`、既定）と実行（`--execute`） | `outputs/logs/` |
| `check_inputs.py` | V1〜V11 に必要な入力の有無とサイズの一覧（中身は開かない） | `outputs/inputs/` |
| `check_v1_v9.py` | V1〜V9 の CPU 検証 | `outputs/hypotheses/` |
| `check_v10_v11.py` | V10〜V11 の再集計 | `outputs/hypotheses/` |
| `regen_flmsec_tables.py` | FLMSEC の表の再生成と、論文の表との照合 | `outputs/tables/` |
| `plot_pareto_curves.py` | safety-utility 曲線 4 枚と、観測事実（`observations.json`） | `outputs/figures/` |
| `ablation_table.py` | アブレーションの k x variant の表 | `outputs/tables/` |
| `build_report.py` | `report.md` の結果の節を組み立てる | `docs/survey_summary/` |

## 実行の順序

1. `run_pipeline.py` を、引数なし（`--dry-run`）で実行する。段階ごとのコマンドが、事前登録の順序
   （inputs、v1_v9、v10_v11、tables、plots、ablation）で表示される。何も実行されず、何も書かれない。
   表示されたコマンドを依頼者に示す。
2. 依頼者の許可を得てから、段階を選んで実行する。例:
   ```
   venv_sst/bin/python v5/scripts/run_pipeline.py --execute --stages inputs --approved-by-user
   ```
   V1〜V9 は、まず範囲を絞る（FIM のキャッシュは 1 ファイルが数十 GB になりうる）:
   ```
   venv_sst/bin/python v5/scripts/run_pipeline.py --execute --stages v1_v9 --approved-by-user \
     --v1-v9-args "--seed 42 --pattern safety+math --layers 0,15,31 --max-tensors 8"
   ```
   範囲を絞った仮説は「判定不能」になる。範囲は出力に記録される。
3. 実行の記録（コマンド、開始と終了の時刻、終了コード）は `outputs/logs/` に残る。
4. 結果が出たら、`build_report.py` で `report.md` の結果の節を作り直す。考察と設計案は、
   `<!-- 手書き: ... -->` の範囲に手書きする（再生成で上書きされない）。

## 出力の読み方

- 表と図には、同名の `*.manifest.json` が付く。使った結果ファイルの一覧（入力パス）、件数、欠損、設定値が入る。
  時刻などの実行ごとに変わる値は入れない（同じ入力から同じ出力が出る。NFR1）。
- 有害判定は、HarmBench Classifier 単独（`harmbench_only`、主軸）と OR 判定（`or_legacy`、再現確認用）の
  両方で表を作る。論文の表との照合（`paper_comparison.md`）では、判定の違いによる差は「判定差」として、
  不一致とは別項目になる。
- v3 に結果が無い条件は `N/A` で、別の条件では代用しない。欠損の一覧は manifest にある。

## テスト

```
venv_sst/bin/python -m pytest v5/tests -q
```

合成データ（`tmp_path`）だけで動き、GPU も実データも使わない。ファイル単位の実行は
`aidlc/spaces/default/intents/261123-survey-summary/construction/code-generation/unit-test-instructions.md` にある。
