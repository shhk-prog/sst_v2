# v3/README.md 改訂計画 (Implementation Plan)

`v3/README.md` を、実際のコードベース（`v3/scripts/` 配下の各種スクリプト、`v3/configs/` の設定ファイル、評価指標、マージ手法、外部ベースライン等）の現行仕様に合わせて網羅的かつ詳細に更新します。

---

## 1. 現状の課題と改訂の目的

既存の `v3/README.md` には以下の不整合および記述不足が存在します：

1. **設定ファイルの不一致**:
   - `configs/config.yaml` のみが記載されているが、実際には `config_main.yaml`, `config_ablation.yaml`, `config_main2.yaml`, `config_ablation2.yaml`, `config_dummy.yaml`, `config_hirundo.yaml` など、実験種別ごとに細分化されている。
2. **スクリプト・モジュール構造の記述不足**:
   - `scripts/mergers/` 配下のモジュール構成（`sst.py`, `fim.py`, `mergekit.py`, `baselines.py`, `utils.py`, `constants.py`）が未記載。
   - `merge_eval_parallel.py`, `run_mergekit_parallel.py`, `run_base_eval_parallel.py` などの並列実行スクリプトや、LED・MatEna・Data-Free重要度計算スクリプト（`compute_datafree_importance.py`, `prepare_led_scores.py`, `elect_led_masks.py`, `matena_fisher.py`）に関する記載がない。
3. **評価ベンチマークとスクリプトの全容不足**:
   - Safety評価（HarmBench, JailbreakBench, StrongReject, WildJailbreak）、Utility評価（GSM8K, Minerva Math500, HumanEval, MBPP, PubMedQA, MedQA, MMLU, IFEval）に加え、AlpacaEval (`eval_alpaca.py`), 指示データセット評価 (`eval_instruction_datasets.py`), Unlearning評価 (`eval_hirundo_unlearning.py`) などの詳細が不足。
4. **詳細な実行方法・オプション解説の不足**:
   - 一括ランナー `run_experiments.py` の各引数（`--stage`, `--config`, `--limit`, `--resume`, `--merge_group`, `--fim_cache_dir` 等）の解説。
   - 各単体スクリプト（`merge.py`, `eval_safety.py`, `eval_utility.py` 等）を個別実行する際のコマンド引数例。
   - 外部ベースライン（SafeMERGE, LED-Merging, MergeAlign, mergekit）のセットアップ手順や注意点。

---

## 2. 改訂後の README.md の構成案

`v3/README.md` を以下の大章構成で再構築・詳細化します：

1. **概要 (Overview)**
   - SST-Merge (Diagonal SST) および Data-Free SST-Merge のコンセプトと実験環境の目的。
2. **ディレクトリおよびモジュール構成 (Directory & Architecture)**
   - `v3/` ディレクトリ全体の完全なツリー。
   - `scripts/mergers/` 配下のモジュール設計と役割の解説。
3. **環境構築と外部ベースラインの準備 (Setup & External Baselines)**
   - 依存パッケージのインストール (`requirements.txt`, `setup_env.sh`)。
   - 仮想環境（`venv_v3`, `venv_led` など）の構成。
   - 外部 GitHub リポジトリ (`baselines/SafeMERGE`, `baselines/LED-Merging`, `baselines/MergeAlign`, `mergekit`) の準備手順。
4. **設定ファイル群 (`configs/`) の解説**
   - 各 YAML ファイル (`config_main.yaml`, `config_ablation.yaml` 等) の用途と主要パラメータの解説（モデルパス、評価タスク、SST比率、スイープ設定等）。
5. **サポートするマージ手法および比較ベースライン (Supported Merging Methods)**
   - 提案手法: `diagonal_sst`, `data_free_sst`
   - 公式 mergekit 経由手法: `ties`, `dare`, `task_arithmetic`, `della`
   - カスタム・外部論文手法: `fisher_weighted`, `matena_fisher`, `safemerge`, `led_merging`, `mergealign`
6. **評価ベンチマークと評価系 (Evaluation Benchmarks)**
   - Safety 評価タスク一覧と指標 (ASR / Safety Score)
   - Utility 評価タスク一覧 (Math, Code, Medical, General)
   - 追加評価スクリプト (AlpacaEval, Instruction Datasets, Unlearning)
7. **詳細な実行方法 (Detailed Usage & Commands)**
   - 7.1 **データ準備**: `data_prep.py`
   - 7.2 **一括パイプライン実行**: `run_experiments.py`（全オプション `--stage`, `--config`, `--limit`, `--resume`, `--merge_group` の詳細解説）
   - 7.3 **個別・手動実行コマンド**: `fine_tuning.py`, `merge.py`, `eval_safety.py`, `eval_utility.py` 等の個別実行例
   - 7.4 **並列実行スクリプト**: `run_base_eval_parallel.py`, `run_mergekit_parallel.py`, `merge_eval_parallel.py`
   - 7.5 **個別要素計算スクリプト**: `compute_datafree_importance.py`, `prepare_led_scores.py`, `elect_led_masks.py`, `matena_fisher.py`
   - 7.6 **解析・プロット・テーブル生成**: `pareto_auc.py`, `generate_tables.py`
8. **実験規約 (`kiro`) とフック (`steering_hook.py`)**
   - 仕様遵守の自動動的検証メカニズム。

---

## 3. 変更対象ファイル

- [MODIFY] [README.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/README.md)

---

## 4. 検証計画

### 手動検証
- 改訂後の `README.md` のすべてのセクション、ファイルパス、コマンド例が実際のコード・オプションと一致しているか整合性を確認。
- 表記・構成が分かりやすく論理的であるかを確認。
