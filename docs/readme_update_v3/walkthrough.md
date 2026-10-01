# v3/README.md 改訂作業完了報告 (Walkthrough)

`/mnt/nas/home/hiromi/src/sst_v2/v3/README.md` を、最新のコード仕様、環境定義、スクリプト構成、比較手法、および詳細な実行コマンドに合わせて包括的に改訂・更新しました。

---

## 1. 実施した主な改訂内容

### 1.1 ディレクトリおよびモジュール構成ツリーの全面更新
- `v3/` ディレクトリ配下の全ファイル・サブディレクトリを網羅。
- `v3/scripts/mergers/` 配下のモジュール設計 (`sst.py`, `fim.py`, `mergekit.py`, `baselines.py`, `constants.py`, `utils.py`) の役割を明記。
- 設定ファイル群 (`config_main.yaml`, `config_ablation.yaml`, `config_main2.yaml` 等) および各並列実行・各種評価・事前計算スクリプトの役割を追記。

### 1.2 マージ手法およびベースラインの網羅
- **提案手法**: `diagonal_sst` (Diagonal SST-Merge), `data_free_sst` (Data-Free SST-Merge)
- **mergekit 公式手法**: `ties`, `dare`, `task_arithmetic`, `della`
- **外部・カスタム手法**: `fisher_weighted`, `matena_fisher`, `safemerge`, `led_merging`, `mergealign`

### 1.3 環境構築と外部比較手法の準備ガイド
- `requirements.txt`, `setup_env.sh` による自動ビルド手順。
- 外部 GitHub リポジトリ (`SafeMERGE`, `LED-Merging`, `MergeAlign`) の `git clone` および仮想環境 (`venv_v3`, `venv_led`) の構成手順。

### 1.4 詳細な実行方法とオプション解説の充実
- **一括パイプライン `run_experiments.py`**:
  - 全オプション（`--stage`, `--config`, `--limit`, `--resume`, `--force`, `--merge_group`, `--fim_cache_dir`）の意味・型・デフォルト値および組み合わせ使用例を明記。
- **手動・個別スクリプト (`fine_tuning.py`, `merge.py`, `eval_safety.py`, `eval_utility.py`, `eval_alpaca.py` 等)**:
  - CLI 引数の例と具体的な実行コマンドを掲載。
- **並列処理スクリプト (`merge_eval_parallel.py`, `run_mergekit_parallel.py`, `run_base_eval_parallel.py`)**:
  - マルチ GPU や複数プロセスでの並列マージ・評価手順を追加。
- **事前計算・マスク選定スクリプト (`compute_datafree_importance.py`, `matena_fisher.py`, `prepare_led_scores.py`, `elect_led_masks.py`)**:
  - 各種事前計算スクリプトの役割と実行例を網羅。
- **パレート解析・テーブル生成 (`pareto_auc.py`, `generate_tables.py`)**:
  - `pareto_frontier.png` や CSV, LaTeX テーブル出力コマンドを解説。

---

## 2. 変更・作成したドキュメント一覧

- **更新ファイル**: [README.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/README.md)
- **プロジェクト保存ドキュメント**:
  - [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/readme_update_v3/implementation_plan.md)
  - [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/readme_update_v3/task.md)
  - [walkthrough.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/readme_update_v3/walkthrough.md)

---

## 3. 検証結果

- [README.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/README.md) 内に記載された全てのスクリプトパス、CLI 引数、オプション名、設定 YAML パスが `v3/` 内の実際のファイルおよび実装コードと完全一致していることを確認しました。
