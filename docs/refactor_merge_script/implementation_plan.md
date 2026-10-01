# リファクタリング計画: `v3/scripts/merge.py` のモジュール分割

`v3/scripts/merge.py` は現在 1530 行を超える巨大なスクリプトとなっており、多様なマージ手法（SST, Mergekit, Fisher, Special Baselines）のロジック、FIM（Fisher Information Matrix）計算、一時モデル構築、メタデータ・ログ記録がすべて1つのファイルに集約されています。

本リファクタリングでは、マージ手法や共通ユーティリティを独立したモジュールに分離し、`v3/scripts/merge.py` を軽量な CLI エントリポイントおよび実行オーケストレーターとして再構築します。

## ユーザーレビュー確認事項

> [!IMPORTANT]
> 既存の CLI インターフェース (`python scripts/merge.py --method ...`) や出力形式・メタデータ仕様は完全に維持されます。既存の実験パイプラインスクリプト（`run_experiments.py` や `test_merge_all.py` など）への破壊的変更はありません。

## 構成案とモジュール設計

`v3/scripts/mergers/` ディレクトリ（新規パッケージ）を作成し、以下のように役割ごとにモジュールを分割します：

```
v3/scripts/
├── merge.py                     # CLI 引数処理、ログ・メタデータ記録、統合実行フロー（スリム化）
└── mergers/                      # [NEW] マージ処理パッケージ
    ├── __init__.py              # 各モジュールからの主要関数・定数のエクスポート
    ├── constants.py             # 定数定義 (MERGEKIT_METHODS, PROPOSED_METHODS, TARGET_MODULE_KEYWORDS 等)
    ├── utils.py                 # モデル読み込み、テンソル操作、SVD変換、一時フルモデル作成ヘルパー
    ├── fim.py                   # Fisher Information Matrix (FIM) の推定・キャッシュ管理
    ├── sst.py                   # Proposed SST手法 (diagonal_sst, data_free_sst) および fisher_weighted
    ├── mergekit.py              # Mergekit 連携処理 (ties, dare, task_arithmetic, della)
    └── baselines.py             # 外部ベースライン連携 (safemerge, mergealign, led_merging, matena_fisher)
```

---

## 変更内容の詳細

### 1. [NEW] `v3/scripts/mergers/constants.py`
- `MERGEKIT_METHODS`, `PROPOSED_METHODS`, `CUSTOM_BASELINES`, `SPECIAL_BASELINES`
- `TARGET_MODULE_KEYWORDS`, `MERGEKIT_METHOD_MAP`, `LAYER_PRIOR_CHOICES`, `FIM_REQUIRED_METHODS` などの定数定義を抽出。

### 2. [NEW] `v3/scripts/mergers/utils.py`
- モデル構築・テンソルヘルパー関数を抽出：
  - `is_target_weight`, `count_target_parameters`, `get_layer_prior`, `load_full_model`
  - `build_models_to_merge`, `require_single_utility`
  - `temp_safety_full_dir`, `temp_util_lora_dir`, `temp_metadata_matches`, `recreate_dir`
  - `create_full_safety_model`, `convert_full_to_lora`
  - `safe_filename_part`, `get_model_short_name`, `is_local_path`, `to_model_ref`, `load_config`, `write_json`, `clear_cuda`

### 3. [NEW] `v3/scripts/mergers/fim.py`
- FIM 関連処理の抽出：
  - `estimate_fim`
  - `build_fim_cache_path`
  - `load_or_estimate_fim`
  - `get_fim_tensor`

### 4. [NEW] `v3/scripts/mergers/sst.py`
- SST 提案手法および Fisher 重み付けマージ処理の抽出：
  - `merge_sst` 関数 (`diagonal_sst`, `data_free_sst`, `fisher_weighted`)

### 5. [NEW] `v3/scripts/mergers/mergekit.py`
- Mergekit 呼び出し用のラッパー処理の抽出：
  - `run_mergekit`

### 6. [NEW] `v3/scripts/mergers/baselines.py`
- 外部ベースライン呼び出し処理の抽出：
  - `run_safemerge`
  - `run_mergealign`
  - `run_led_merging`, `infer_led_order`, `validate_led_config`
  - `run_matena_fisher` (外部モジュール `matena_fisher.py` のラッパー呼び出し)

### 7. [NEW] `v3/scripts/mergers/__init__.py`
- `mergers` パッケージの統合エクスポート。`merge.py` や外部モジュールからのインポートを容易化。

### 8. [MODIFY] `v3/scripts/merge.py`
- `mergers` パッケージから必要な定数・関数をインポート。
- CLI 引数パース (`parse_args`, `apply_config_defaults`)、ロガー (`RuntimeLogger`)、メタデータ出力 (`save_success_metadata`, `write_failed_metadata`, `write_complexity_summary`)、統合制御 (`execute_merge`, `main`) のみに整理し、コード量を約 300 行程度に削減。

---

## 動作確認・検証計画

### 自動テスト / スクリプト検証
1. 構文チェック: `python -m py_compile` で全作成ファイルおよび `merge.py` の文法エラーを確認。
2. 動作確認テスト:
   - `v3/scripts/test_merge_all.py` の全テストまたは個別のモックテストの実行による検証。
   - `python v3/scripts/merge.py --help` による CLI 引数パースの検証。

### 手動確認
- `mergers` パッケージの構成とインポート関係が正しく動作することを確認。
