# 修正内容の確認 (Walkthrough): `v3/scripts/merge.py` のモジュール分割

`v3/scripts/merge.py` のマージ処理および関連ユーティリティを独立したパッケージ `v3/scripts/mergers/` に分離・整理しました。

## 変更内容のまとめ

### 新規作成パッケージ・モジュール: `v3/scripts/mergers/`

1. **[constants.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers/constants.py)**
   - マージ手法名 (`MERGEKIT_METHODS`, `PROPOSED_METHODS`, `CUSTOM_BASELINES`, `SPECIAL_BASELINES`) やレイヤープライア・対象モジュールキーワード (`TARGET_MODULE_KEYWORDS`) などの定数を集約・管理。

2. **[utils.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers/utils.py)**
   - モデル読み込み (`load_full_model`)、ターゲットパラメータ検出 (`is_target_weight`, `count_target_parameters`)、レイヤープライア算出 (`get_layer_prior`)、SVDによるフルモデル→LoRA変換 (`convert_full_to_lora`)、一時モデル生成・キャッシュ管理 (`create_full_safety_model`, `recreate_dir`) などの汎用関数を抽出。

3. **[fim.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers/fim.py)**
   - Fisher Information Matrix (FIM) の推定 (`estimate_fim`)、キャッシュ管理 (`build_fim_cache_path`, `load_or_estimate_fim`)、FIM テンソル取得処理 (`get_fim_tensor`) を抽出。

4. **[sst.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers/sst.py)**
   - Proposed SST 手法 (`diagonal_sst`, `data_free_sst`) および `fisher_weighted` マージを行う核心ロジック `merge_sst()` を分離。

5. **[mergekit.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers/mergekit.py)**
   - `mergekit-yaml` を介した Mergekit 連携手法 (`ties`, `dare`, `task_arithmetic`, `della`) のラッパー関数 `run_mergekit()` を抽出。

6. **[baselines.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers/baselines.py)**
   - 外部ベースラインマージ手法の連携ロジックを抽出・集約：
     - `run_safemerge`
     - `run_mergealign`
     - `run_led_merging`, `infer_led_order`, `validate_led_config`
     - `run_matena_fisher_baseline` (外部モジュール `matena_fisher.py` のラッパー呼び出し)

7. **[__init__.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/mergers/__init__.py)**
   - パッケージの統合インポート・エクスポート定義。

---

### リファクタリング対象ファイル: `v3/scripts/merge.py`

- **[merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge.py)**
  - モジュール分離によりコード行数を約 **1530行から約400行** へと大幅に削減。
  - CLI 引数解析 (`parse_args`, `apply_config_defaults`)、実行プロファイリング (`RuntimeLogger`)、複雑性・失敗・成功メタデータの保存、高レベルなフロー制御 `execute_merge()` に特化させました。

---

## 検証結果

- **構造・整合性確認**: 各モジュール間および `merge.py` からのインポート依存関係が完全に整合していることを確認しました。
- **CLI 互換性**: 既存の呼び出しオプション (`--method`, `--config`, `--pattern`, `--alpha`, `--output_dir` 等) および出力メタデータ構造に変更はなく、互換性が完全に保たれています。
