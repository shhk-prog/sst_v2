# コード構成: v3

本ファイルは、ディレクトリ構成とファイル分類の唯一の一覧である。各コンポーネントの責務は `component-inventory.md`、外部依存は `dependencies.md` を参照。

## ディレクトリ構成（スキャン範囲）

```text
v3/
├── README.md                 # 日本語の全体ガイド（構成、手法、実行方法）。SST の式は §3-4
├── requirements.txt
├── configs/                  # 実験設定 YAML（7 ファイル）
├── scripts/
│   ├── merge.py              # 単一 merge の CLI（734 行）
│   ├── fine_tuning.py        # Safety LoRA の SFT
│   ├── data_prep.py          # FIM 用・評価用データの作成（286 行）
│   ├── run_experiments.py    # 全手法の merge と評価の起動（SHALLOW）
│   ├── run_mergekit_parallel.py  # mergekit 系 4 手法の並列 merge（226 行）
│   ├── merge_eval_parallel.py    # merge 済みモデルの並列評価。merge はしない（1052 行）
│   ├── run_base_eval_parallel.py
│   ├── slurm_*.sh, submit_*.sh   # SLURM 投入
│   ├── steering_hook.py      # 実験規約の動的検査（tests/ に同一ファイルあり）
│   ├── fix_*_jsons_fast.py   # 結果 JSON の事後修正
│   ├── mergers/              # merge のコアパッケージ（sst.py 202 行、fim.py 161 行、utils.py 317 行ほか）
│   ├── merging/              # LED スコア、MatEna Fisher、Data-Free 重要度の事前計算
│   ├── eval/                 # 評価スクリプト
│   ├── analysis/             # 集計と論文表の生成（約 55 ファイル）
│   ├── fixes/, tools/, tests/
├── evaluators/               # 第三者リポジトリ（gitlink）: HarmBench, jailbreakbench, strong_reject
└── 論文/
    ├── FLMSEC/               # 大規模評価の論文（NeurIPS 2026 形式、tables/table1-4.tex, appendix.tex）。SST は意図的に未掲載
    ├── DLSP_hiromi2/         # secure merge の提案論文（Mistral-7B 設定、main.tex 3,240 行, tables.tex, figures/, appen_fig/）
    └── SAGAI_EN_sst/         # SST-Merge の提案論文（IEEEtran、main.tex 2,119 行、tables.tex 72 行（未使用、DLSP と同一）, main.bib, figures/, appen_fig/）
```

スキャン範囲外（未オープン）: `baselines/`, `models/`, `cache/`, `data/`, `logs/`, `docs/`, `kiro/`, `venv_*`。`results/vllm/` は構造のみ確認した（`api-documentation.md` の「結果ファイル契約」）。`論文/SAGAI_EN_sst/` の `main.bib`, `figures/`, `appen_fig/` は開いていない。表の再生成用に今後作る `v5/` は、まだ存在しない（`code-quality-assessment.md` の技術的負債 1）。

## リポジトリ外の前身（v1 / v2。読むだけ、スナップショット外）

ワークスペース直下（`sst_v2/`）にある `v1/`（約 778M）と `v2/`（約 47G）である。v3 のコードは import しない。系譜と差分は `architecture.md` の「v1 → v2 → v3 の系譜」。重み、`.pt`、`.safetensors`、`.bin`、`models/`、`lm-evaluation-harness/`、`mergekit/`（外部ライブラリ）、`logs/`、`data/` の中身、結果 JSON の大半は開いていない（結果は論文との照合に必要なセルだけ読んだ）。`._*` と `.DS_Store` は無視した。

```text
v1/                           # SST-Merge の提案論文の数値を出した実験（Llama-3.1-8B-Instruct, LoRA A5/A6/A7）
├── core/
│   ├── sst_merge.py          # FIM・GEVP・Additive の本体（1144 行）。ベースは L42
│   ├── sst_merge_interpolation.py  # 補間型（390 行）。sst_merge.py の FIMCalculator と GEVPSolver を再利用
│   └── sst_merge_data_free.py      # Data-Free（626 行）。LoRA 重みの二乗を proxy にする
├── scripts/
│   ├── merging/              # 掃引ドライバ（run_all_merges{,_hard,_interpolation,_adapter_based,_full}.py, run_data_free_merge.py）と baseline_merge.py（TA / TIES / DARE）
│   ├── FT/                   # LoRA の FT（safety_tune.py, repliqa_tune.py, alpaca_tune.py）と各評価（jailbreak_eval.py, repliqa_eval.py, alpaca_eval.py）
│   ├── evaluation/, analysis/, visualization/, sst_eval_pipeline/（exp1〜exp5）, benchmarks/, utilities/
│   └── fim_validation_*.py, analyze_*.py   # FIM の検証と劣化分析
├── eval/{finetuned,merged}/  # 結果 JSON。merged は baseline / sst_merge / interpolation / data_free と、先頭が空白の ` A7-7ep/`
├── all_eval_results_summary.json, latex_tables_output.tex, detailed_config_analysis.txt, generate_latex_from_json.py  # 集計と表
├── run_all_experiments.sh, run_sst_merge_comparison.sh  # 存在しないパスを呼ぶ古いシェル（論文の数値の生成元ではない）
├── tests/test_data_free_merge.py, test_*.py  # 現状では動かない（import パスの不整合）
├── data/（response_dataframe.csv, backdoor_jailbreak.json）, requirements.txt, README.md
└── archive/, scratch/, logs/ # 名前と構成だけ確認（archive は旧版の experiments / analysis / sst_merge_v2〜v4 など）

v2/                           # Llama-2-7B の merge の足場と Llama-3 系の FT ベースライン（AAAI-27 向け）
├── scripts/
│   ├── merge/                # sst_merge_core.py（関数のみ）, run_sst_merge.py（ダミーのデモ）, merge_llama2_sst_suite.py（ストリーミング merge）, run_mergekit.sh, run_official_safemerge.py
│   ├── fine_tuning/          # run_lora_ft.py と各評価、Phase 2 のスクリプト
│   ├── data_prep/, evaluation/, analysis/pareto_auc.py
│   └── steering_hook.py, test_steering_hook.py, setup_env.sh
├── configs/aaai27/           # llama2_sst_experiment.yaml（Llama-2-7B と 3 ドメインモデル）、config_example.yaml（Llama-3.1-8B-Instruct）
├── docs/fine_tuning_phase2_results/   # Phase 2 の結果（implementation_plan.md, task.md, walkthrough.md）
├── run_all_experiments_suite.sh, README.md, requirements.txt
├── kiro/{specs,steering}     # v2 配下のプロジェクト固有の設定（名前のみ確認）
└── data/, models/, results/, logs/, lm-evaluation-harness/, mergekit/   # 名前のみ（results は Llama-3.1-8B-Instruct、Llama-3-8B-Instruct、lm_eval_raw）
```

## ファイル分類

| 分類 | ファイル |
|---|---|
| Service/UseCase（merge アルゴリズム） | `scripts/mergers/sst.py`, `scripts/mergers/fim.py`, `scripts/merging/matena_fisher.py`, `scripts/merging/compute_datafree_importance.py`, `scripts/merging/prepare_led_scores.py`, `scripts/merging/elect_led_masks.py` |
| Adapter（外部実装の呼び出し） | `scripts/mergers/mergekit.py`, `scripts/mergers/baselines.py` |
| Controller/Handler（CLI エントリ） | `scripts/merge.py`, `scripts/fine_tuning.py`, `scripts/data_prep.py`, `scripts/eval/*.py`, `scripts/analysis/*.py` |
| オーケストレーション | `scripts/run_experiments.py`, `scripts/merge_eval_parallel.py`, `scripts/run_mergekit_parallel.py`, `scripts/run_base_eval_parallel.py`, `scripts/slurm_*.sh`, `scripts/submit_*.sh` |
| Utility/Helper | `scripts/mergers/utils.py`, `scripts/mergers/constants.py`, `scripts/tools/*.py`, `scripts/fixes/*.py`, `scripts/fix_*_fast.py` |
| Middleware（規約チェック） | `scripts/steering_hook.py` |
| Configuration | `configs/*.yaml`, `requirements.txt`, `scripts/setup_env.sh` |
| Test | `scripts/tests/test_steering_hook.py`, `scripts/tests/test_merge_all.py` |
| Static/Asset（論文） | `論文/FLMSEC/**/*.tex`, `論文/DLSP_hiromi2/**`, `論文/SAGAI_EN_sst/**` |

## コードのパターン

- **手法の分岐は文字列で行う**: `constants.py` の 4 グループ（`MERGEKIT_METHODS`, `PROPOSED_METHODS`, `CUSTOM_BASELINES`, `SPECIAL_BASELINES`）に応じて、`merge.py` の `execute_merge` が if/elif で分岐する。`merge_eval_parallel.py` は同じグループを集合として再定義している（L10-20）
- **命名規則が契約になっている**: 出力ディレクトリ名と結果ファイル名に（実験名, 手法, パターン, α, n, k, 比率, variant, mask, layerwise, seed）を埋め込み、集計側はファイル名を `_` で分割して解析する
- **設定の既定値は `merge.main` から**: `merge.py` は引数を省略すると `merge.main` を読む。アブレーションの条件はオーケストレータが組み立て、引数で明示して渡す
- **パラメータ名ごとの merge**: SST と Fisher 系は θ₀ の `named_parameters` を順に回し、形状と名前で分岐する（`sst.py` L33-105）
- **再開可能な実行**: 各 CLI は既存 JSON の `completed` と件数を確認して処理を飛ばす（`--resume`, `--force`）
- **事後修正スクリプト**: 評価後に結果 JSON を書き換えるスクリプトがある（humaneval のインデント、mbpp、ifeval、gibberish の再判定など）
- コメントとドキュメント文字列は主に日本語
- （v1、リポジトリ外）**設定はスクリプト先頭の定数**: ドライバが `merge_pairs`、`alpha_values`、`sst_k_values` などをファイル内に持ち、`input("gpu num:")` で GPU を尋ねる。結果名は `{pair}_sst_{interp_}k{k}{_lw}{_nogevp}_a{α}`（`run_all_merges_interpolation.py` L124-133）、Data-Free は `..._data_free{_interp}_k{k}{_lw}_a{α}{_topk{k}}`（`run_data_free_merge.py` L271-284）の形で、旧ラベルと新ラベルが同じフォルダに混在する
