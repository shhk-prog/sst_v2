# Reverse Engineering Timestamp

## Run Record

- Date: 2026-11-23T12:46:53Z
- Commit: 4959ba3151ceb574b63e202bd66a0a2317afb53b

### 実行 1（初回）
- 実施方法: 開発者エージェント単独（collaborators off）でのスキャンと統合。FOCUSED スキャン、深さ Minimal
- 対象: リポジトリ `v3`。スナップショットのパス `README.md`, `configs`, `scripts`, `evaluators`, `論文` の範囲内
- 備考: `results/vllm/` はスナップショット外のため、構造とファイル名だけを確認した（SHALLOW）。`baselines/`、`models/`、`cache/`、`data/`、`logs/`、`venv_*` などは開いていない。プロジェクトのテスト、ビルド、プログラムは実行していない

### 実行 2（改訂、2026-11-23）
- 契機: 承認ゲートでの差し戻し（SST-Merge の詳細検証、研究の位置付けの記録、表生成を `v5/` で新規実装する方針の記録）
- 実施方法: 開発者エージェント単独（collaborators off）。既存の CURRENT ストア（`kind: partial`）に統合する FOCUSED スキャン。深さ Minimal、ただし SST-Merge の検証は詳細に実施
- 対象: スナップショットのパス `README.md`, `configs/`, `scripts/mergers/`, `scripts/merge.py`, `scripts/fine_tuning.py`, `scripts/eval/eval_safety.py`, `scripts/eval/eval_utility.py`, `scripts/analysis/generate_flmsec_hyo.py`, `論文/FLMSEC/Formatting_Instructions_For_NeurIPS_2026/neurips_2026.tex`, `論文/DLSP_hiromi2/main.tex`, `論文/DLSP_hiromi2/tables.tex`, `scripts/merge_eval_parallel.py`, `scripts/run_mergekit_parallel.py`, `scripts/data_prep.py`
- 新たに精読: `scripts/merge_eval_parallel.py`, `scripts/run_mergekit_parallel.py`, `scripts/data_prep.py`, `論文/DLSP_hiromi2/main.tex`, `論文/DLSP_hiromi2/tables.tex`。`scripts/mergers/`, `scripts/merge.py`, `configs/` は行単位で再読
- リポジトリ外で読んだもの（SHALLOW、ブリーフの許可による）: HF キャッシュのモデル設定 `~/.cache/huggingface/hub/models--{meta-llama--Llama-2-7b-hf, WizardLMTeam--WizardMath-7B-V1.0, vanillaOVO--WizardCoder-Python-7B-V1.0, medalpaca--medalpaca-7b}/snapshots/*/config.json`。リポジトリ相対のパスではないため、下の `shallow.paths` には入れていない
- 開いていないもの: `baselines/`、`models/` の重み、`cache/` のテンソル、`data/`、`logs/`、`venv_*`、すべての `.pt` と blob。`scripts/run_experiments.py` は grep だけ（SHALLOW）
- 実行していないもの: プロジェクトのテスト、ビルド、プログラム。数値の確認は `code-quality-assessment.md` の「後続段階で要検証」に回した

### 実行 3（改訂、2026-11-23）
- 契機: 承認ゲートでの差し戻し（SST-Merge の提案論文は `v3/論文/SAGAI_EN_sst` にある、という指摘）
- 実施方法: 開発者エージェント単独（collaborators off）。既存の CURRENT ストア（`kind: partial`）への focused merge。深さ Minimal。中断した前回セッションのステージング（8 ファイル）を論文と照合して修正し、本ファイルを新たに作成
- 新たに精読: `論文/SAGAI_EN_sst/main.tex`（定式化 L476-773、実験設定 L781-809、付録の実験設定 L1059-1164、結果の表と考察は引用箇所を照合）、`論文/SAGAI_EN_sst/tables.tex`（全体。`main.tex` から読み込まれず、`論文/DLSP_hiromi2/tables.tex` と同一）、`論文/SAGAI_EN_sst/main.bib`（secure merge の出典 `11050841` の項目のみ）
- 開いていないもの: `論文/SAGAI_EN_sst/figures/`, `論文/SAGAI_EN_sst/appen_fig/`（画像）、`._*` ファイル
- 実行していないもの: プロジェクトのテスト、ビルド、プログラム、LaTeX のコンパイル

### 実行 4（改訂、2026-11-23）
- 契機: 承認ゲートでの差し戻し（4 回目。人の原文: 「v1-v3まで網羅的に確認して論文と照合して」）。別の AI による照合メモ 7 項目が貼り付けられ、検証対象の主張として扱った
- 実施方法: 開発者エージェント単独（collaborators off）。既存の CURRENT ストア（`kind: partial`）への focused merge。深さ Minimal（照合は詳細に実施）。v3 側は公開済みストアを土台にし、v1 と v2 を読んで、論文・v1・v2・v3 の 4 者の照合を行った
- **v1 と v2 を読んだ事実**: ワークスペース直下の `v1/`（約 778M）と `v2/`（約 47G）を読んだ。どちらも v3 リポジトリの外にあり、スナップショット（許可された path 集合）の外なので、下の `analyzed.paths` と `shallow.paths` には入れていない。読むだけで、プログラム、テスト、ビルド、GPU ジョブ、LaTeX のコンパイルは実行していない。数値は結果ファイル（JSON、`.tex`、`.txt`）を読んで確かめた
- v1 で精読したもの: `core/sst_merge.py`（全体）、`core/sst_merge_interpolation.py`（`SSTMergeInterpolation` の merge と FIM 計算）、`core/sst_merge_data_free.py`（全体）、`scripts/merging/`（`run_all_merges_interpolation.py`、`run_data_free_merge.py`、`run_all_merges_hard.py` の FIM と merge の部分、`baseline_merge.py` の TA / TIES / DARE、`merge_adapters.py` の `sst_merge`、`run_all_merges.py` と `run_all_merges_adapter_based.py` の設定部）、`scripts/FT/`（`safety_tune.py`、`repliqa_tune.py`、`alpaca_tune.py` の設定部と `jailbreak_eval.py`、`repliqa_eval.py`、`alpaca_eval.py` の評価部）、`run_all_experiments.sh`、`run_sst_merge_comparison.sh`、`latex_tables_output.tex`、`detailed_config_analysis.txt`、`generate_latex_from_json.py`、`README.md`、`requirements.txt`。結果は論文の代表セルに対応するファイルだけを読んだ（`eval/merged/{baseline,sst_merge,interpolation,data_free}` と ` A7-7ep/` の指標の値、`all_eval_results_summary.json` の該当項目）
- v1 で名前と構成だけ確認したもの: `archive/`、`scratch/`、`logs/`（`grep` でアダプター適用のログの有無だけ確認、見つからず）、`scripts/` の他のサブディレクトリ、`eval/` の結果ファイルの大半。重み、`.pt`、`.safetensors`、`.bin` は v1 に無く（`models/` は無い）、開いていない
- v2 で精読したもの: `README.md`、`run_all_experiments_suite.sh`、`scripts/merge/`（`sst_merge_core.py`、`run_sst_merge.py`、`merge_llama2_sst_suite.py`）、`configs/aaai27/*.yaml`、`requirements.txt`、`docs/fine_tuning_phase2_results/walkthrough.md`（冒頭）、`scripts/fine_tuning/run_lora_ft.py` と `scripts/analysis/pareto_auc.py` の冒頭
- v2 で名前と構成だけ確認したもの: `kiro/`（v2 配下のプロジェクト固有の設定。`specs/sst-merge-aaai27`、`steering/`）、`results/`、`models/`、`data/`、`logs/`、`lm-evaluation-harness/`、`mergekit/`（外部ライブラリ）、`.cache/`。開いていないもの: `v2/logs/`、`results/` の中身、`models/` の中身
- v3 側で再読したもの: `scripts/mergers/sst.py` の λ とマスクと補間の部分（L136-193）、`scripts/merge.py` の F_h 推定（L568-584）。それ以外は公開済みストアの記述を保持した。`論文/SAGAI_EN_sst/main.tex` は表（L1188-1285, L1371-1395）を読んだ
- 本実行で訂正した前回までの記述: (1) Data-Free の「比がほぼ一定」（v1 の実装は Utility と Safety の重みの二乗を別々に求める）、(2) 「SAGAI の数値を出したコードは v3 に見つかっていない」（v1 にある）、(3) 「F_h を Safety モデルで評価するのは v3 固有のずれ」（v1 の原実装からの引き継ぎ）、(4) 論文の A5 Data-Free k=10% と k=20% の表が同一なのは貼り間違いの可能性、という記述（v1 の旧ラベルの結果自体が同一）
- 実行していないもの: プロジェクトのテスト、ビルド、プログラム、GPU ジョブ、LaTeX のコンパイル。v1 / v2 のアダプターの実体や実行ログを開いていないため、FIM の推定にアダプターが載る処理の実害は未確認（`code-quality-assessment.md` の V12 以降）

## Scope of Analysis

```yaml
scope_version: 1
kind: partial
intent: survey-summary
fingerprint: 2145f8ffa805c34d8914dd97fbd6da63330011fa
analyzed:
  paths:
    - README.md
    - configs/
    - scripts/mergers/
    - scripts/merge.py
    - scripts/fine_tuning.py
    - scripts/eval/eval_safety.py
    - scripts/eval/eval_utility.py
    - scripts/analysis/generate_flmsec_hyo.py
    - 論文/FLMSEC/Formatting_Instructions_For_NeurIPS_2026/neurips_2026.tex
    - scripts/merge_eval_parallel.py
    - scripts/run_mergekit_parallel.py
    - scripts/data_prep.py
    - 論文/DLSP_hiromi2/main.tex
    - 論文/DLSP_hiromi2/tables.tex
    - 論文/SAGAI_EN_sst/
  components:
    - mergers-sst
    - mergers-fim
    - mergers-mergekit
    - mergers-baselines
    - mergers-utils
    - merge-cli
    - safety-lora-training
    - eval-safety
    - eval-utility
    - flmsec-table-generator
    - experiment-configs
    - flmsec-paper
    - eval-orchestrator
    - mergekit-orchestrator
    - fim-data-prep
    - dlsp-paper
    - sagai-sst-paper
    - v1-sst-core
    - v1-merge-drivers
    - v1-baseline-merge
    - v1-eval-scripts
    - v1-results-and-tables
    - v2-sst-merge-scaffold
    - v2-finetuning-baselines
shallow:
  paths:
    - scripts/
    - evaluators/
    - 論文/
    - results/vllm/
```
