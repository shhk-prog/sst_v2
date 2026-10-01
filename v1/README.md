# SST-Merge

**Safety–Utility alignment via Generalized Eigenvalue Problem**

SST-Merge は、大規模言語モデル（LLM）のマージングにおいて現れる **Safety Tax**（安全性を上げると有用性が落ちやすい、というトレードオフ）を緩和するためのフレームワークです。  
**Fisher Information Matrix（FIM）** と **一般化固有値問題（Generalized Eigenvalue Problem: GEVP）** を組み合わせ、「安全性の改善に効きやすく、有用性への悪影響が相対的に小さい」更新方向を優先するマスクや重み付けを求めます。

---

## 背景とアイデア（概要）

- **Safety Tax**: 安全性特化アダプタと有用性特化アダプタを単純に足し合わせたり平均したりすると、ジョークレイク耐性と Alpaca 等の有用性指標が両立しにくいことがあります。
- **GEVP の役割**: 有害側・無害側に対応する FIM（実装上は $F_{\mathrm{harm}}$ と $F_{\mathrm{benign}}$、コード内では `F_h` / `F_b` など）を用いて $F_{\mathrm{harm}} v = \lambda F_{\mathrm{benign}} v$ を解き、**レイリー商** $R(v) = (v^\top F_{\mathrm{harm}} v) / (v^\top F_{\mathrm{benign}} v)$ が大きい方向を「安全寄与が大きく、有用性コストが相対的に小さい」方向として利用します。
- **Data-Free 版**: 実データで FIM を直接計算できない場合でも、LoRA 重みなどからの代理（サロゲート）で順位や近似を使う **Data-Free SST-Merge** が用意されています（詳細は `docs/` および `core/sst_merge_data_free.py`）。

---

## 提供されるマージの型

実装・実行ガイド（`docs/03_implementation/execution_guide.md`）に沿って、主に次の三系統があります。

| 種類 | 概要 |
|------|------|
| **加算型（Additive）** | 実データで FIM を計算し、`Utility + α × mask × Safety` 形式でマージ。 |
| **補間型（Interpolation）** | 実データで FIM を計算し、`(1−α) × Utility + α × mask × Safety` 形式（Task Arithmetic 系との対応が取りやすい）。 |
| **Data-Free** | データ不要の近似で加算型・補間型の両方をサポート。 |

---

## リポジトリ構成（ルート）

| パス | 内容 |
|------|------|
| `core/` | SST-Merge の中核実装（加算・補間・Data-Free）。 |
| `scripts/merging/` | 一括マージやベースライン比較などの実行スクリプト。 |
| `scripts/evaluation/` | Alpaca / Jailbreak / RepliQA 等の評価スクリプト。 |
| `scripts/FT/` | LoRA ファインチューニング・各種ベンチ評価用スクリプト。 |
| `scripts/sst_eval_pipeline/` | 論文・再現性向けの評価パイプライン（下記）。 |
| `scripts/analysis/`、`scripts/visualization/` | 結果集計・可視化。 |
| `data/` | 実験・評価用データ（CSV / JSON 等）。 |
| `docs/` | 理論、実装手順、実験記録、論文ドラフトなど **一式のドキュメント索引**（`docs/README.md`）。 |
| `tests/` | `pytest` 向けテスト（例: Data-Free マージ）。 |
| `archive/` | 旧版スクリプト・設定・実験コードの保管（参照・復元用）。 |

### `scripts/sst_eval_pipeline/`（厳密評価パイプライン）

| スクリプト | 目的（設計上の位置づけ） |
|------------|--------------------------|
| `exp1_safety_gain_correlation.py` | $F_h$ と実測 Safety ゲインの相関検証 |
| `exp2_fisher_ratio_pareto.py` | Fisher 比とパレート効率 |
| `exp3_data_free_surrogate.py` | Data-Free サロゲートの検証 |
| `exp4_statistical_reproducibility.py` | 統計的再現性 |
| `exp5_robustness_ablation.py` | ロバスト性・アブレーション |

必要ならベースモデル・LoRA パス等を `--base_model` などで指定します（各ファイルの `argparse` を参照）。

---

## 要件

- **Python**: 3.10 以上を推奨（プロジェクトが依存する PyTorch / transformers の一般的な要件に準拠）。
- **GPU**: FIM 計算・マージ・評価は CUDA 環境を前提とした構成が多いです（CPU のみでも動く部分はありますが、実用上は GPU 推奨）。
- **Hugging Face**: ベースモデルやデータセットの取得に `transformers` / `datasets` を利用します。ゲート付きモデルを使う場合は `huggingface-cli login` 等が必要です。
- **オプション**: メモリ・速度のため **Flash Attention 2**（`flash-attn`）を入れることがあります。ビルドが必要な場合は `requirements.txt` 内のコメントを参照してください。

---

## インストール

```bash
cd SST-main
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -U pip
pip install -r requirements.txt
```

開発時はテスト実行に `pytest` が含まれています。

```bash
pytest tests/
```

---

## 使い方の入口（推奨ドキュメント）

このリポジトリは **`docs/` にクイックスタート・実行手順・理論・結果が集約**されています。まず次を読むと全体像が掴みやすいです。

| 目的 | ドキュメント |
|------|----------------|
| すぐ試す・並列実験など | [`docs/01_quickstart/QUICKSTART.md`](docs/01_quickstart/QUICKSTART.md) |
| 補間型 / Data-Free の具体的コマンドと設定 | [`docs/03_implementation/execution_guide.md`](docs/03_implementation/execution_guide.md) |
| スクリプト一覧・役割 | [`docs/03_implementation/script_reference.md`](docs/03_implementation/script_reference.md) |
| 理論の整理 | [`docs/02_theory/`](docs/02_theory/) |
| ドキュメント全体の索引 | [`docs/README.md`](docs/README.md) |

### マージ実行の例（補間型）

`execution_guide.md` に従い、`scripts/merging` で補間型一括マージを実行する流れが説明されています。

```bash
cd scripts/merging
python3 run_all_merges_interpolation.py
# 実行時に GPU 番号の入力を求められる場合があります（スクリプト実装に依存）
```

スクリプト内の **`merge_pairs`**、**`alpha_values`**、**`sst_k_values`**、データパス（例: `data/response_dataframe.csv`、Utility 用 Hugging Face データセット名）を、利用環境に合わせて編集してください。

### 評価パイプラインの実行例

```bash
python scripts/sst_eval_pipeline/exp2_fisher_ratio_pareto.py \
    --base_model "meta-llama/Meta-Llama-3-8B-Instruct" \
    --safety_lora "path/to/safety_lora" \
    --utility_lora "path/to/utility_lora"
```

（他の実験スクリプトは追加で `--fh_path` / `--fb_path` 等が必要な場合があります。）

### ルートの `run_all_experiments.sh` について

リポジトリ直下の `run_all_experiments.sh` は、**特定環境向けのパス・仮想環境（`cd` / `source sst/bin/activate`）がハードコード**されています。別マシンで使う場合はパスを書き換えるか、`archive/experiments/` 付近のスクリプトと組み合わせて自分の環境用に調整してください。

---

## コア実装（`core/`）：内容・出力物

スクリプトから `main` 相当として呼ばれるクラス・関数が集約されています。単体実行時はファイル先頭の **`model_id`・`merge_pairs`・`output_dir`** などを編集します。

| ファイル | 処理内容 | 主な出力先・生成物 |
|----------|-----------|----------------------|
| **`sst_merge.py`** | 実データから FIM を推定し GEVP を解き、**加算型**マスクで Utility LoRA と Safety LoRA を合成。`FIMCalculator`・`GEVPSolver`・`SSTMerge` を含む。 | 既定は `./merge_model/`（リポジトリ直下から実行した場合）。**マージ済みアダプター**: `adapter_model.safetensors`、`adapter_config.json`、`merge_metadata.json`。**フルモデル保存時**: Hugging Face 形式のシャード・`tokenizer`。**入力データ**: Safety FIM 用に `data/response_dataframe.csv`、Utility は Hugging Face データセット（設定依存）。 |
| **`sst_merge_interpolation.py`** | **補間型** `(1−α)×Utility + α×masked Safety`。`SSTMergeInterpolation` がコア。 | 呼び出し側スクリプトが `save_merged_adapter`／`save_pretrained` のパスを決める（通常は `scripts/merging/run_all_merges_interpolation.py` 経由）。生成ファイル形式は加算型と同様（safetensors + メタデータ）。 |
| **`sst_merge_data_free.py`** | 学習データなしで LoRA 重みから FIM 近似し、**Data-Free** 加算／補間を実行。`SSTMergeDataFree`、`FIMCalculatorDataFree` 等。 | **`save_merged_adapter`**: `adapter_model.bin`（PyTorch）、`adapter_config.json`（コピー）。フル変換は別スクリプト側。 |

---

## `scripts/merging/`：一括マージ・変換

パスはスクリプト内の **`project_root` / 相対パス** 前提です。リポジトリルートが `SST-main` のとき、多くの既定値は **`models/merged/...`** および **`models/finetuned/...`** です。

| ファイル | 内容 | 出力先・生成物 |
|----------|------|----------------|
| **`run_all_merges_interpolation.py`** | 補間型 SST のグリッド探索（`alpha`、`k`、layer-wise、GEVP の組合せ）。ベースライン変換含む。 | **アダプター**: `models/merged/interpolation/adapters/merge_adapters_interpolation/`。**フルモデル**: `models/merged/interpolation/full/merge_model_interpolation/`。名前例: `{pair}_sst_interp_k{k}_lw_a{α}_...`。実行時に GPU 番号入力あり。 |
| **`run_data_free_merge.py`** | Data-Free の加算／補間をグリッド実行し、必要ならフルモデル化。 | **アダプター**: `models/merged/data_free/adapters/merge_model_data_free/`。**フル**: `models/merged/data_free/full/merge_model_data_free_full/`。 |
| **`run_all_merges_adapter_based.py`** | ベースライン（Task Arithmetic / TIES / DARE 等）と SST を **アダプター保存 → フル変換** の2段で実行。 | `models/merged/sst_merge/adapters/merge_adapters/` と `models/merged/sst_merge/full/merge_model/`（スクリプト内定数）。 |
| **`run_all_merges_hard.py`** | **Hard top‑k**（`sst_k`）を含む SST とベースラインの大量実行。 | `models/merged/sst_merge/full/merge_model`、`adapters/merge_adapters`。フル: `config.json` 等。スキップ時は既存成果物を利用。 |
| **`run_all_merges.py`** / **`run_all_merges_full.py`** | 比較的シンプルな SST（layer-wise フラグ中心）とベースラインの一括実行。 | 既定 `../../models/merged/sst_merge/full/merge_model`（実行 cwd により実パスは変化）。 |
| **`merge_adapters.py`** | 複数マージ手法を指定ペアに適用（比較用）。 | `../../models/merged/sst_merge/full/merge_model/{pair}_{method}/`（ファイル先頭コメント参照）。同上で **safetensors + `merge_metadata.json` + README**。 |
| **`baseline_merge.py`** | `CustomBaselineMerger` による TIES / DARE / Task Arithmetic 等とアダプター保存。`__main__` で一括実行可。 | 既定 `../../models/merged/sst_merge/full/merge_model`。 |
| **`convert_adapters_to_full.py`** | 単体 LoRA（A5/A6/A7 等）をベースにマージして **フル重み** 化。 | **`../../models/finetuned/full/FT_model_full/{出力名}/`**（`config.json`・モデルシャード・tokenizer）。 |
| **`temp_merge_config.py`** | 単発の比較マージ（開発・デバッグ向け）。 | `../../models/merged/sst_merge/full/compare/` 配下のサブフォルダ。 |

---

## `scripts/evaluation/`：マージ済みモデルの評価

各 `merge_*_eval.py` は **`merged_model_path`** と **`model_name`**（出力ファイル名の接頭辞）をスクリプト内で指定します。**出力は既定でリポジトリ相対の `eval/merged/...`** です。

| ファイル | 内容 | 出力ファイル・場所 |
|----------|------|---------------------|
| **`merge_alpaca_eval.py`** | Alpaca 形式データでの生成と ROUGE 系スコア。 | `eval/merged/sst_merge/{model_name}_alpaca_eval_results.json`（`output_dir` 変更可）。 |
| **`merge_repliqa_eval.py`** | RepliQA 系ユーティリティ評価。 | `..._repliqa_eval_results.json`（同上）。 |
| **`merge_jailbreak_eval.py`** | ジョークレイクプロンプトに対する拒否率など（TrustLLM 分類器があれば利用）。 | `..._jailbreak_eval_results.json`。JSON 内に `metrics`・各プロンプト結果。 |
| **`run_all_evals.py`** | `models/merged/interpolation/full/...` 等を走査し、ペアに応じて Alpaca または RepliQA + Jailbreak を ** subprocess で個別評価スクリプトに渡す**。 | 既定 **`eval/merged/interpolation/`**（スクリプト内 `output_dir`）。各モデルごとに上記 3 種の JSON。 |
| **`run_all_evals_interpolation.py`** | 補間マージ結果専用の一括評価。 | **`eval/merged/interpolation/`** に同様の `*_eval_results.json`。 |
| **`eval_specific_model.py`** | 指定モデルに対し `merge_repliqa_eval` / `merge_jailbreak_eval` を叩く簡易ラッパ。 | 呼び出したスクリプト側の `output_dir` に依存。 |
| **`eval_sft_checkpoints.py`** | チェックポイント名ごとに `eval_specific_model.py` を起動。 | 同上。 |
| **`eval_logic_bench.py`** | ロジックベンチの精度評価。 | **`scripts/benchmarks/logic_eval_results.json`**（固定パスで `open`）。 |
| **`evaluate_multidimensional_utility.py`** | 既存の `*_eval_results.json` を集約し、多次元ユーティリティの Markdown レポート生成（OpenAI API オプション）。 | **`--base_dir` 等で入力 JSON を指定**。出力 Markdown パスはスクリプト内 **環境固有のデフォルト** のため、利用時は引数・コード内パスを必ず自分用に変更。 |
| **`summarize_data_free_results.py`** | `eval/merged/data_free` の JSON を読み、設定別に指標を整理（主に表示・集計）。 | 標準出力中心。ファイル出力は実装依存（リポジトリ内では集計ロジックのみの場合あり）。 |

---

## `scripts/FT/`：ファインチューニングと単体モデル評価

| ファイル | 内容 | 出力先・生成物 |
|----------|------|----------------|
| **`safety_tune.py`** / **`alpaca_tune.py`** / **`repliqa_tune.py`** / **`gsm8k_tune.py`** / **`gsm8k_tune_alpaca.py`** | 各タスク用 LoRA 学習（設定はスクリプト内）。 | 多くは **`./results`** または **`./FT_model/...`** 形式で `save_pretrained`（実行ディレクトリ依存）。 |
| **`run_safety_ft_baseline.py`** / **`run_safety_ft_mixed.py`** | 安全性 FT のバリアント。 | `trainer` の `output_dir` にチェックポイント・adapter。 |
| **`alpaca_eval.py`** / **`repliqa_eval.py`** / **`gsm8k_eval.py`** | 単体アダプター／モデルの Alpaca / RepliQA / GSM8K 評価。 | 既定 **`results/finetuned/{adapter_name}_*_eval_results.json`**（`../../results/finetuned` は `scripts/FT` からの相対）。 |
| **`jailbreak_eval.py`** | `--output_dir` 指定可（デフォルト `../../results/finetuned/jailbreak`）。 | `{adapter_name}_jailbreak_eval_results.json`。 |

---

## `scripts/sst_eval_pipeline/`：論文向け検証（実装状況に注意）

研究計画用の **実験番号付きスクリプト**です。一部は **TODO／プレースホルダ** で、現状は標準出力に期待フォーマットを示すだけのものがあります（本番評価ループは `pass` やコメントアウト）。

| ファイル | 設計上の内容 | 出力 |
|----------|----------------|------|
| **`exp1_safety_gain_correlation.py`** | $F_h$ 由来のゲインと実測 JB 耐性の相関。 | 現状はログ出力のみ（`SSTMerge` 初期化まで）。 |
| **`exp2_fisher_ratio_pareto.py`** | 各基準（SST、f\_h のみ、1/f\_b 等）のパレート比較。 | 実装完了時はパレート曲線データ・図を想定。現状はコンソールのプレースホルダ。 |
| **`exp3_data_free_surrogate.py`** | FIM 順位と Data-Free 順位の一致度。 | 相関・Top‑k 一致を想定。現状プレースホルダ。 |
| **`exp4_statistical_reproducibility.py`** | シード違いの平均・分散・CI。 | 設計コメントに JSON／表出力を記載。現状ダミー乱数。 |
| **`exp5_robustness_ablation.py`** | FIM サンプル数・データセット転移の頑健性。 | 同上、プレースホルダ中心。 |

---

## `scripts/analysis/`・`scripts/visualization/`・その他

**分析**（多くは **`eval/` やルートの `*.json` を入力**）:

| ファイル | 内容 | 主な出力 |
|----------|------|----------|
| **`collect_all_results.py`** | `eval/` 以下の `*_eval_results.json` を再帰集約。 | 実行ディレクトリに **`all_eval_results_summary.json`**、**`experiment_summary.md`**。 |
| **`generate_complete_tables.py`** / **`generate_comprehensive_report.py`** | 集約 JSON から長い表・総合レポート。 | **`complete_results_tables.md`**、**`comprehensive_report.md`**（スクリプトは `all_eval_results_summary.json` を読む想定）。 |
| **`generate_markdown_tables.py`** / **`generate_data_dependent_tables.py`** / **`generate_data_free_tables.py`** | サブセット向け表生成。 | Markdown または標準出力（入力パスは各ファイル先頭付近）。 |
| **`merge_eval_to_csv.py`** / **`summarize_merge_eval.py`** / **`summarize_results.py`** | JSON→CSV やサマリー表。 | CSV / ログ（`summarize_results.py` は `../../results/merged/sst_merge` 等を参照）。 |
| **`analyze_merge_results.py`** | α スイープ等の可視化と CSV。 | **`alpha_sweep_comparison.png`**、**`safety_utility_tradeoff.png`**、`summary_table.csv`、`all_results.csv`（`output_dir` はファイル末尾で指定、一部デフォルトが別環境パス）。 |
| **`analyze_fim_overlap.py`** | FIM 関連スコアの重なり分析。 | **`scripts/benchmarks/fim_overlap_results.json`**。 |

**可視化**:

| ファイル | 内容 | 主な出力 |
|----------|------|----------|
| **`plot_eval_results.py`** | 集約データからベースライン vs SST の棒グラフ等。 | 既定 **`docs/merge_eval_summary/`** に `*_baseline_methods.png`、`*_sst_methods.png`。 |
| **`visualize_merge_results_fixed.py`** / **`pareto_frontier_analysis.py`** / **`visualize_sst_merge_detailed.py`** | 性能 vs α、パレート、詳細比較図。 | 既定 **`docs/evaluation_results_202602/`** など（`output_dir` 引数・変数で変更可）。PNG。 |

**プロジェクト直下の補助スクリプト**:

| ファイル | 内容 | 出力 |
|----------|------|------|
| **`scripts/collect_all_metrics.py`** | 複数ディレクトリから Jailbreak / RepliQA 指標を抽出して一覧化。 | 標準出力（手法別に抵抗率・ROUGE を表示）。 |
| **`scripts/fim_validation_ablation.py`** | FIM スコアに基づく prune / modify の介入実験。 | **`scripts/fim_validation_ablation_results.json`**。 |
| **`scripts/fim_validation_pruning.py`** | 類似の検証（設定はファイル内）。 | JSON またはログ（実装参照）。 |
| **`scripts/benchmarks/measure_overhead.py`** | 計算オーバーヘッド計測。 | コンソール（時間・メモリ）。 |

---

## `tests/`

| ファイル | 内容 | 出力 |
|----------|------|------|
| **`test_data_free_merge.py`** | 小さなダミー LoRA で `SSTMergeDataFree` / `FIMCalculatorDataFree` の smoke test。 | 成功時はログのみ（ファイル成果物なし）。**実行時は `core` をパスに含めるか、`core` をカレントにしてインポートする必要がある場合あり**。 |

---

## `run_all_experiments.sh`（ルート）

| 項目 | 内容 |
|------|------|
| **処理** | （設定次第で）SST 実験 → ベースライン → mergekit ベースライン → `compare_all_methods.py`。 |
| **ログ** | `logs/sst_merge_{TIMESTAMP}.log` 等。 |
| **結果** | `results/exp1_safety_utility/`、`results/baseline_experiments/`、`results/comparison/`（スクリプト内 echo 参照）。**リポジトリ内の `experiments/` は `archive/` 側にあり、ルートのシェルは別マシン用パスがハードコードされているため、そのままでは動かないことがあります。** |

---

## 主な実験結果・サマリー

集約された評価サマリーは **`experiment_summary.md`**（リポジトリ直下）および **`docs/05_results/`** にあります。数値の前提条件・設定の違いは各レポート内の表・記述を参照してください。

---

## ライセンス・引用

論文・実装の引用形式は、公開ポリシーに合わせて `docs/07_paper/` を参照してください（ドラフトの言語別ファイルあり）。

---

## 関連リンク（リポジトリ内）

- [ドキュメント索引 `docs/README.md`](docs/README.md)
- [評価データセット一覧 `docs/01_quickstart/EVALUATION_DATASETS.md`](docs/01_quickstart/EVALUATION_DATASETS.md)
