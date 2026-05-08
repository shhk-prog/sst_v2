# スクリプトリファレンス (`script_reference.md`)

`sst_merge_v5` プロジェクトにおける主要なスクリプトの役割、入力、および出力を整理します。

## 1. コアロジック (`core/`)
マージ手法の数学的・アルゴリズム的な実装です。

| スクリプト | 役割 | 入力 | 出力 |
| :--- | :--- | :--- | :--- |
| `sst_merge.py` | SST-Merge（GEVPベース）のメイン実装 | Base Model, Utility/Safety Adapters | マージ済みモデルオブジェクト |
| `sst_merge_data_free.py` | 学習データ不要（Data-Free）版の実装 | LoRA Adapters (A, B matrices) | マージ済みモデル |
| `sst_merge_interpolation.py` | α値による補間とGEVPを組み合わせた実装 | 各種アダプタ、α値 | マージ済みモデル |

## 2. マージ実行 (`scripts/merging/`)
各種手法を用いて実際にモデルをマージし、ディスクに保存するためのスクリプト群です。

| スクリプト | 役割 | 入力 | 出力 |
| :--- | :--- | :--- | :--- |
| `run_all_merges_adapter_based.py` | 設定（k, alpha等）を変えて一括マージ | アダプタパス | `models/merged/sst_merge/` |
| `run_data_free_merge.py` | Data-Free手法での一括マージ | アダプタパス | `models/merged/data_free/` |
| `run_all_merges_interpolation.py` | 補間型マージの一括実行 | アダプタパス | `models/merged/interpolation/` |
| `baseline_merge.py` | TA, TIES, DAREの実行 | アダプタパス | `models/merged/baseline/` |

## 3. 評価実行 (`scripts/evaluation/`)
マージ済みモデルのベンチマーク性能を測定します。

| スクリプト | 役割 | 入力 | 出力 |
| :--- | :--- | :--- | :--- |
| `run_all_evals.py` | 指定ディレクトリ内の全モデルを評価 | モデルディレクトリ | `results/merged/` 下のJSON |
| `merge_jailbreak_eval.py` | Jailbreak耐性（Safety）の専門評価 | モデルパス | `*_jailbreak_eval_results.json` |
| `merge_alpaca_eval.py` | AlpacaEval（Utility）の評価 | モデルパス | `*_alpaca_eval_results.json` |
| `merge_repliqa_eval.py` | RepliQA（Utility）の評価 | モデルパス | `*_repliqa_eval_results.json` |

## 4. 分析・検証 (`scripts/` & `scripts/analysis/`)
実験データの集計や、手法の正当性（FIMの妥当性など）を検証します。

| スクリプト | 役割 | 入力 | 出力 |
| :--- | :--- | :--- | :--- |
| `collect_all_results.py` | 全評価JSONを集計し、一つのJSONに統合 | `results/` | `all_eval_results_summary.json` |
| `fim_validation_ablation.py` | **[実験B, C]** FIMの正当性・他指標比較 | アダプタ、評価用データ | `fim_validation_ablation_results.json` |
| `analyze_utility_loss.py` | 過剰拒否とROUGE低下の相関分析 | 評価JSON | `utility_loss_analysis.csv` |
| `analyze_fim_overlap.py` | 異なるデータ間でのFIMの重なり(Jaccard)計測 | 各種データセット | 標準出力・ログ |
| `generate_comprehensive_report.py` | 論文・レポート用の包括的サマリー生成 | 集計済みJSON | `docs/` 下のレポート |

## 5. 微調整・比較用 (`scripts/FT/`)
ベースとなるアダプタの作成や、マージとの直接比較用SFTを実行します。

| スクリプト | 役割 | 入力 | 出力 |
| :--- | :--- | :--- | :--- |
| `run_safety_ft_baseline.py` | **[実験A]** Utilityモデルへの直接Safety FT | Utility Adapter + Safety Data | 学習済みチェックポイント |
| `alpaca_tune.py` / `repliqa_tune.py` | 各種Utilityアダプタの作成 | Base Model + Data | Utility Adapters |
| `safety_tune.py` | Safetyアダプタの作成 | Base Model + Data | Safety Adapters |

## 6. 可視化 (`scripts/visualization/`)
結果の傾向をグラフ化します。

| スクリプト | 役割 | 入力 | 出力 |
| :--- | :--- | :--- | :--- |
| `pareto_frontier_improved.py` | Trade-off Curve（パレートフロンティア）の描画 | 集計済みJSON | `pareto_frontier.png` |
| `visualize_sst_merge_detailed.py` | k値やlayer-wiseの影響を可視化 | 詳細評価結果 | 各種プロット |
