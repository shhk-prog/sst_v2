# SST-Merge V3 実験環境 (SST-Merge & Data-Free SST-Merge Experimentation Suite)

本ディレクトリは、良性タスク性能（Utility）と安全性能（Safety）の競合（Safety Tax）を最適化問題として扱い、安全パッチモデルをマージする手法 **SST-Merge** およびそのデータフリー近似 **Data-Free SST-Merge** の包括的な実験・評価・解析環境です。

Llama-2-7B ベースの各ドメインモデル（Math, Code, Medical）および独自に学習する Safety model を用い、公式の比較手法ライブラリや外部論文の再現コードを取り入れ、パラメータスイープ、アブレーションスタディ、並列実行、Pareto Frontier 解析を一括・個別で実行できます。

---

## 1. ディレクトリおよびモジュール構成

```text
v3/
├── README.md                      # 本ファイル（構成・規約・環境・詳細実行ガイド）
├── requirements.txt               # Python 依存関係パッケージ定義
├── configs/                       # 実験設定ファイル群（YAML）
│   ├── config_main.yaml           # 主実験（SST-Merge vs 全比較手法）の設定パラメータ
│   ├── config_ablation.yaml        # アブレーションスタディ用設定パラメータ
│   ├── config_main2.yaml          # 拡張実験 / 別パラメータ構成設定
│   ├── config_ablation2.yaml       # 拡張アブレーション設定
│   ├── config_dummy.yaml          # テスト・デバッグ用軽量設定
│   └── config_hirundo.yaml        # Unlearning / 応答アライメント用実験設定
├── scripts/                       # スクリプト群
│   ├── run_experiments.py         # 全工程（FT, マージ前評価, マージ, マージ後評価, 解析）の一括自動実行ランナー
│   ├── merge.py                   # 単一モデルマージの CLI エントリーポイント
│   ├── merge_eval_parallel.py     # マージおよび評価の並列一括実行スクリプト
│   ├── run_mergekit_parallel.py   # mergekit 経由手法の並列一括実行スクリプト
│   ├── run_base_eval_parallel.py  # ベースモデル / ドメインモデルの並列一括評価スクリプト
│   ├── fine_tuning.py             # Safety model (LoRA) の SFT 学習スクリプト
│   ├── data_prep.py               # FIM 推定用データセット配置スクリプト
│   ├── setup_env.sh               # 依存環境の自動ビルド
│   ├── eval/                      # 評価・ベンチマーク系スクリプト
│   │   ├── eval_safety.py         # 安全性（ASR / Safety Score）評価
│   │   ├── eval_utility.py        # 有用性（lm-evaluation-harness）評価
│   │   ├── eval_alpaca.py         # AlpacaEval 2 評価
│   │   ├── eval_instruction_datasets.py # 指示追従（Evol-Instruct-Code, MedAlpaca）評価
│   │   ├── eval_hirundo_unlearning.py # Unlearning 評価
│   │   └── check_harmbench_results.py # HarmBench 結果確認
│   ├── merging/                   # マージ手法・スコア計算系
│   │   ├── compute_datafree_importance.py # Data-Free SST 重要度計算
│   │   ├── matena_fisher.py       # MatEna Fisher 重み計算・マージ
│   │   ├── prepare_led_scores.py  # LED-Merging 用スコア準備
│   │   └── elect_led_masks.py     # LED-Merging 用マスク選定
│   ├── analysis/                  # 解析・集計・視覚化系
│   │   ├── pareto_auc.py          # Pareto Frontier 解析およびプロット生成
│   │   ├── generate_tables.py     # 結果テーブル CSV / LaTeX 自動生成
│   │   └── count_dataset_sizes.py # データセットサイズ計測
│   ├── tools/                     # モデル・環境構築ユーティリティ
│   │   ├── create_dummy_models.py # パイプライン検証用ダミーモデル生成
│   │   └── create_full_model.py   # LoRA アダプタのマージ済み Full model 変換
│   ├── tests/                     # テスト・動的検証フック系
│   │   ├── steering_hook.py       # 実験規約遵守チェック・動的フック
│   │   ├── test_steering_hook.py  # フック動的検証用ユニットテスト
│   │   └── test_merge_all.py      # 全マージ手法の統合テスト
│   ├── fixes/                     # 修正・トラブルシューティングユーティリティ
│   │   ├── fix_all_alpaca_eval_jsons.py
│   │   ├── fix_humaneval_jsons.py
│   │   ├── fix_ifeval_jsons.py
│   │   ├── fix_mbpp_jsons.py
│   │   ├── fix_mmlu_pro_jsons.py
│   │   ├── clean_failed_results.py
│   │   ├── clean_ifeval_results.py
│   │   └── verify_mbpp_fix.py
│   └── mergers/                   # マージ用モジュールパッケージ
│       ├── __init__.py            # モジュールエクスポート
│       ├── sst.py                 # SST-Merge (Diagonal SST / Data-Free SST) コアロジック
│       ├── fim.py                 # 対角 Fisher 情報行列 (FIM) の推定・キャッシュ機能
│       ├── mergekit.py            # mergekit YAML 動的生成およびサブプロセス実行ラッパー
│       ├── baselines.py           # 外部比較手法 (SafeMERGE, MergeAlign, Fisher等) 実行ラッパー
│       ├── constants.py           # 定数・手法定義・デフォルトパラメータ
│       └── utils.py               # モデル読み込み・LoRA変換・テンソル演算ヘルパー
├── data/                          # データセット配置先
│   ├── response_dataframe.csv     # Safety SFT 用データセット
│   ├── fim/                       # FIM 推定用 Benign / Harmful プロンプトデータ
│   └── eval/                      # 評価用データセット
├── models/                        # モデル出力先
│   ├── safety_lora/               # 学習済み Safety model LoRA アダプタ
│   ├── temp_safety_full/          # 一時展開した Full Safety モデル
│   └── merged/                    # マージ済みモデルの保存先
├── results/                       # 評価結果出力先
│   ├── debug_limit320/            # 実験・評価結果 (ベースモデル / マージモデル)
│   │   ├── base/                  # ベースモデル・単体モデルの評価結果
│   │   └── merged/                # マージモデルの評価結果 (seed -> pattern -> method)
│   │       ├── seed42/
│   │       │   ├── safety+math/
│   │       │   ├── safety+code/
│   │       │   ├── safety+medical/
│   │       │   └── safety+math+code+medical/
│   │       ├── seed43/
│   │       └── seed44/
│   └── pareto/                    # Pareto AUC 解析結果 CSV およびプロット (`pareto_frontier.png`)
├── baselines/                     # 外部比較手法リポジトリ配置先
│   ├── SafeMERGE/                 # SafeMERGE 公式リポジトリ
│   ├── LED-Merging/               # LED-Merging 公式リポジトリ
│   └── MergeAlign/                # MergeAlign 公式リポジトリ
├── kiro/                          # 実験規約定義ディレクトリ
├── venv_v3/                       # 標準実験用 Python 仮想環境
└── venv_led/                      # LED-Merging 専用 Python 仮想環境
```

---

## 2. 実験規約 (`kiro`) と検証フック (`steering_hook.py`)

本実験環境は、`/mnt/nas/home/hiromi/src/sst_v2/v3/kiro` に定義された実験規約を厳格に遵守して実装されています。カスタムコードによる勝手な近似を排除し、公式および著者公開の実装を直接実行します。

### 実験規約の遵守ルール
1. **比較ベースラインの再現**:
   - **mergekit公式マージ (`ties`, `dare`, `task_arithmetic`, `della`)**: 自前のマージ演算を一切排除し、公式 `mergekit-yaml` を生成して実行。
   - **外部 GitHub リポジトリ (`SafeMERGE`, `LED-Merging`, `MergeAlign`)**: 著者公開の公式 Python コードをそのまま呼び出す。
   - **Fisher-weighted averaging / MatEna**: 公式定義に忠実な Fisher 重み付き平均式を適用。
2. **動的検証フック (`steering_hook.py`)**:
   - スクリプト実行時に自動でロードされ、規約違反（未許可のモック処理、不正なパラメータ計算など）を動的に検知・ブロックします。

---

## 3. サポートするマージ手法一覧

### 3.1 提案手法 (Proposed Methods)
- **`diagonal_sst` (Diagonal SST-Merge)**:
  - 対角 Fisher 情報行列を用いて、有害タスク応答への感度 $F_h$ と良性タスク応答への感度 $F_b$ の比率 $\lambda_i = \frac{f_{h,i}}{f_{b,i} + \varepsilon}$ を重要度計量としてマージ。
- **`data_free_sst` (Data-Free SST-Merge)**:
  - 訓練データセットを一切使用せず、Safety モデルの重み差分の二乗比率 $\hat{\lambda}_i = \frac{(\Delta_{h,i})^2}{(\Delta_{b,i})^2 + \varepsilon}$ を Proxy として用いてマージ。

### 3.2 公式 `mergekit` 経由ベースライン
- **`task_arithmetic`**: Task Arithmetic (Ilharco et al.)
- **`ties`**: TIES-Merging (Yadav et al.)
- **`dare`**: DARE (Yu et al.)
- **`della`**: DELLA (Sharma et al.)

### 3.3 カスタム・外部論文比較ベースライン
- **`fisher_weighted`**: Fisher-weighted averaging (Matena & Raffel et al.)
- **`matena_fisher`**: MatEna の Fisher 情報重み付き統合 (`scripts/matena_fisher.py`)
- **`safemerge`**: SafeMERGE (Yang et al.) — `baselines/SafeMERGE` 経由
- **`led_merging`**: LED-Merging (Lu et al.) — `baselines/LED-Merging` 経由 (`venv_led` 環境)
- **`mergealign`**: MergeAlign (Hassan et al.) — `baselines/MergeAlign` 経由

---

## 4. アブレーションスタディ (Ablation Study) 仕様

SST-Merge の設計要素を評価するため、`configs/config_ablation.yaml` で以下のスイープが可能です。

### 4.1 重要度計量 (`sst_ratio`)
- **`Fh/Fb` (提案)**: $\lambda_i = \frac{f_{h,i}}{f_{b,i} + \varepsilon}$
- **`Fh only`**: $\lambda_i = f_{h,i}$ ($F_b$ を無視)
- **`1/Fb only`**: $\lambda_i = \frac{1}{f_{b,i} + \varepsilon}$ ($F_h$ を無視)
- **`magnitude`**: $\lambda_i = |\Delta_{s,i}|$ (重み差分の絶対値)
- **`random`**: $\lambda_i \sim \text{Uniform}(0, 1)$

### 4.2 マージ変種 (`variant` & `mask`)
- **`additive`**: $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \alpha (w_{\mathrm{layer}} \odot m \odot \Delta_s)$ (加算)
- **`interpolation`**: $\theta_{\mathrm{merged}} = (1-w)\theta_{\mathrm{util}} + w\theta_{\mathrm{safe}}$ (補間)
- **`hard mask`**: 上位 $k$ 割合の座標を $1$、それ以外を $0$ とする二値マスク
- **`layer_wise` / `layer_prior`**: レイヤー優先度バイアス（`uniform`, `sin`, `linear`, `exp`）

### 4.3 FIM サンプルサイズスイープ
- サンプル数 $N \in \{50, 100, 250, 500\}$ による推定精度とマージ性能の影響評価。

---

## 5. 評価ベンチマーク (Evaluation Suite)

### 5.1 Safety 評価 (`eval_safety.py`)
- **HarmBench**: 多様な有害プロンプトに対する脱獄成功率 (ASR) 評価
- **JailbreakBench**: 標準化脱獄攻撃に対する耐性評価
- **StrongReject**: 強固な拒絶応答判定基準による評価
- **WildJailbreak**: 野生の複雑な脱獄プロンプトによる評価

### 5.2 Utility 評価 (`eval_utility.py`)
- **Math ドメイン**: `gsm8k`, `minerva_math500`
- **Code ドメイン**: `humaneval`, `mbpp`
- **Medical ドメイン**: `pubmedqa`, `medqa_4options`
- **General (汎用)**: `mmlu`, `ifeval`

### 5.3 追加・拡張評価スクリプト
- **`eval_alpaca.py`**: AlpacaEval ベンチマークによる応答品質評価
- **`eval_instruction_datasets.py`**: Evol-Instruct-Code および MedAlpaca の指示追従評価
- **`eval_hirundo_unlearning.py`**: Hirundo アンラーニング指標による安全応答アライメント評価

---

## 6. 環境構築と外部リポジトリの準備

### 6.1 依存パッケージのインストール
標準環境 `venv_v3` を作成して依存パッケージをインストールします：

```bash
# 仮想環境の作成と有効化
python3 -m venv venv_v3
source venv_v3/bin/activate

# 基本パッケージのインストール
pip install -r v3/requirements.txt

# 自動ビルドスクリプトによる lm-evaluation-harness および mergekit のセットアップ
bash v3/scripts/setup_env.sh
```

### 6.2 外部比較手法リポジトリの準備
`baselines/` ディレクトリ配下に公式リポジトリをクローンします：

```bash
mkdir -p baselines
git clone https://github.com/aladinD/SafeMERGE baselines/SafeMERGE
git clone https://github.com/MqLeet/LED-Merging baselines/LED-Merging
git clone https://github.com/hammoudhasan/MergeAlign baselines/MergeAlign
```

### 6.3 LED-Merging 専用環境の構築 (オプション)
LED-Merging の実行に特定依存（`venv_led`）が必要な場合：

```bash
python3 -m venv venv_led
source venv_led/bin/activate
pip install -r baselines/LED-Merging/requirements.txt
deactivate
```

---

## 7. 実行方法およびコマンドガイド

### 7.1 データセットの準備
FIM 推定用および評価用のデータを配置・生成します：

```bash
python v3/scripts/data_prep.py
```

---

### 7.2 一括パイプライン自動実行 (`run_experiments.py`)
全工程（FT -> マージ前評価 -> マージ -> マージ後評価 -> パレート解析）を自動実行します。

```bash
# 1. 主実験の一括実行 (全モデル・全手法)
python v3/scripts/run_experiments.py --config configs/config_main.yaml

# 2. 高速テスト・動作確認 (各評価タスクのサンプル数を 10 件に制限)
python v3/scripts/run_experiments.py --config configs/config_main.yaml --limit 10

# 3. アブレーションスタディの一括実行
python v3/scripts/run_experiments.py --config configs/config_ablation.yaml

# 4. 特定ステージのみの実行 (--stage)
# 選択可能ステージ: all, ft, base_eval, merge, merge_eval, pareto
python v3/scripts/run_experiments.py --stage merge --config configs/config_main.yaml

# 5. 特定手法グループのみ実行 (--merge_group)
python v3/scripts/run_experiments.py --merge_group mergekit --config configs/config_main.yaml
python v3/scripts/run_experiments.py --merge_group non_mergekit --config configs/config_main.yaml

# 6. 中断からの再開 (--resume) / 強制再実行 (--force)
python v3/scripts/run_experiments.py --config configs/config_main.yaml --resume
```

#### `run_experiments.py` の主要オプション一覧

| 引数 | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `--config` | str | `configs/config_main.yaml` | 実験設定 YAML ファイルのパス |
| `--stage` | str | `all` | 実行ステージ (`all`, `ft`, `base_eval`, `merge`, `merge_eval`, `pareto`) |
| `--skip_ft` | flag | False | Fine-Tuning ステージをスキップ |
| `--skip_base_eval` | flag | False | ベースモデル評価をスキップ |
| `--skip_merge` | flag | False | マージ処理をスキップ |
| `--skip_merge_eval` | flag | False | マージモデル評価をスキップ |
| `--limit` | int | 10 | 評価問題数の上限制限（`0` で全数実行） |
| `--resume` | flag | False | 既存の評価結果 JSON が存在する場合に処理を再開 |
| `--force` | flag | False | キャッシュを無視して強制再実行 |
| `--merge_group` | str | `all` | マージ手法の絞り込み (`all`, `mergekit`, `non_mergekit`) |
| `--fim_cache_dir` | str | `cache/fim` | FIM 推定値のキャッシュ保存先 |

---

### 7.3 個別・手動スクリプト実行

#### (1) Safety Model の Fine-Tuning (`fine_tuning.py`)
`data/response_dataframe.csv` を用いて LoRA 安全モデルを学習します：

```bash
python v3/scripts/fine_tuning.py \
    --base_model meta-llama/Llama-2-7b-hf \
    --data_path data/response_dataframe.csv \
    --output_dir models/safety_lora
```

#### (2) 手動モデルマージ (`merge.py`)
単一設定でモデルマージを実行します：

```bash
# Diagonal SST-Merge の手動実行
python v3/scripts/merge.py \
    --config configs/config_main.yaml \
    --method diagonal_sst \
    --pattern safety+math \
    --alpha 0.5 \
    --k 0.2 \
    --sst_ratio Fh/Fb \
    --variant interpolation \
    --mask_type "hard mask" \
    --output_dir models/merged/manual_diagonal_sst

# Data-Free SST-Merge の手動実行
python v3/scripts/merge.py \
    --config configs/config_main.yaml \
    --method data_free_sst \
    --pattern safety+code \
    --alpha 0.4 \
    --k 0.2 \
    --output_dir models/merged/manual_data_free_sst

# TIES-Merging (mergekit) の手動実行
python v3/scripts/merge.py \
    --config configs/config_main.yaml \
    --method ties \
    --pattern safety+medical \
    --alpha 0.5 \
    --output_dir models/merged/manual_ties
```

#### (3) 個別評価スクリプトの実行

```bash
# Safety 評価 (JailbreakBench)
python v3/scripts/eval_safety.py \
    --model_path models/merged/manual_diagonal_sst \
    --config configs/config_main.yaml \
    --task jailbreakbench \
    --limit 50 \
    --output_file results/raw/eval_safety_manual.json

# Utility 評価 (GSM8K)
python v3/scripts/eval_utility.py \
    --model_path models/merged/manual_diagonal_sst \
    --config configs/config_main.yaml \
    --tasks gsm8k \
    --limit 50 \
    --output_file results/raw/eval_utility_manual.json

# AlpacaEval 評価
python v3/scripts/eval_alpaca.py \
    --model_path models/merged/manual_diagonal_sst \
    --config configs/config_main.yaml \
    --limit 20 \
    --output_file results/raw/eval_alpaca_manual.json
```

---

### 7.4 並列実行スクリプト

大規模スイープを高速化するため、マルチ GPU / 並列プロセス実行が可能です。

```bash
# 1. ベースモデルの並列評価
python v3/scripts/run_base_eval_parallel.py --config configs/config_main.yaml --limit 100

# 2. mergekit 手法の並列マージ実行
python v3/scripts/run_mergekit_parallel.py --config configs/config_main.yaml

# 3. マージおよび評価の統合並列パイプライン
python v3/scripts/merge_eval_parallel.py --config configs/config_main.yaml --limit 100
```

---

### 7.5 事前計算・準備スクリプト

```bash
# Data-Free SST 重要度の事前計算
python v3/scripts/compute_datafree_importance.py --config configs/config_main.yaml

# MatEna Fisher 情報の計算
python v3/scripts/matena_fisher.py --config configs/config_main.yaml

# LED-Merging スコア計算およびマスク選定
python v3/scripts/prepare_led_scores.py --config configs/config_main.yaml
python v3/scripts/elect_led_masks.py --config configs/config_main.yaml
```

---

### 7.6 集計・Pareto Frontier 解析・テーブル生成

評価結果 JSON が蓄積された後、Pareto 境界の算出、グラフ描画、集計表の作成を行います。

```bash
# Pareto Frontier 解析およびプロット生成
python v3/scripts/pareto_auc.py
```

- **出力**:
  - プロット画像: `results/pareto/pareto_frontier.png`
  - パレート集計 CSV: `results/pareto/pareto_metrics_summary.csv`

```bash
# 論文・レポート用テーブルの自動生成
python v3/scripts/generate_tables.py
```

- **出力**:
  - `results/processed/summary_table.csv`
  - `results/processed/summary_table.tex` (LaTeX 形式)

---

## 8. テストおよび動作検証

実験パイプライン全体の正常動作を確認するための各種テストユーティリティ：

```bash
# 1. 動的検証フックのユニットテスト
python v3/scripts/test_steering_hook.py

# 2. 全マージ手法の単体動作テスト (軽量ダミーモデル使用)
python v3/scripts/test_merge_all.py

# 3. 不完全・途中で失敗した評価 JSON の削除
python v3/scripts/clean_failed_results.py
```
