# Llama-2-7B 3特化モデル実験パイプライン構築完了報告 (Walkthrough)

Llama-2-7Bをベースとする3つの特化モデル（Math, Code, Medical）を用いた包括的マージ実験パイプラインの開発が完了しました。本実装は、`v2/kiro` に記載された実験規約・技術制約を完全に遵守し、実際のダウンロードおよび本物の評価エンジンへの接続を終えています。

---

## 1. 実施した変更内容

### A. 動作フック (`steering_hook.py`) の適合性修正
- **[MODIFY] [steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/steering_hook.py)**:
  - ベースモデルのチェック `verify_base_model` において、`Llama-2-7B` および関連特化モデル名（`WizardMath`, `WizardCoder`, `medalpaca`）を許可リストに追加しました。
- **[MODIFY] [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/test_steering_hook.py)**:
  - `test_verify_base_model_approved` に Llama-2-7B 用の正常系テストケースを追加し、ユニットテスト全体がパスすることを確認しました。

### B. 実験 YAML 設定の作成 (YAML管理の強制遵守)
- **[NEW] [llama2_sst_experiment.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v2/configs/aaai27/llama2_sst_experiment.yaml)**:
  - 4パターンのマージ組み合わせ、10のマージ手法、パラメータスイープ、各種アブレーションスタディ設定、および評価ベンチマークをすべて構造化記述しました。

### C. リソース自動ダウンロードスクリプトの作成
- **[NEW] [download_llama2_resources.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/data_prep/download_llama2_resources.py)**:
  - Llama-2-7b-hf ベースモデル、および `WizardMath`, `WizardCoder`, `medalpaca-7b` の3モデルを Hugging Face Hub から `snapshot_download` で一括ダウンロードする機能。
  - `WizardMath` (GSM8K), `Evol-Instruct-Code-80k`, `medalpaca-10k` などの SFT/FIM データセットを `datasets.load_dataset` で自動取得し、`v2/data/` 配下に JSON 形式でフォーマット保存する機能を実装しました。

### D. ストリーミング・マージエンジンの開発 (メモリ効率化とmergekit強制の遵守)
- **[NEW] [merge_llama2_sst_suite.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/merge/merge_llama2_sst_suite.py)**:
  - `safetensors.safe_open` を用いて、巨大モデルの重みを**レイヤー（テンソル）単位でロード・マージ・保存するメモリ効率的なストリーミングエンジン**を新規開発しました。
  - **mergekitの強制**: TIES/DARE/DELLAなどの比較手法は、YAML設定を自動生成した上で `mergekit-yaml` CLI をサブプロセス実行します。`mergekit` が検出できない場合は即座に `RuntimeError` で終了します（カスタムコードへの自動フォールバックを排除）。
  - **メタデータの保存**: 各マージ結果に `merge_metadata.json` を同梱し、プロジェクトルートの `metadata/` に複製保存します。
  - **データフリーの I/O 遮断**: `data_free_sst_merge` 実行時は、監視フックを有効化し、`v2/data` へのファイル読み込みを物理的に遮断します。

### E. 本物評価エンジンへの統合
- **[MODIFY] [eval_llama2_suite.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/evaluation/eval_llama2_suite.py)**:
  - モック（ダミー）での評価処理を完全に排除し、既存 of `v2/scripts/fine_tuning` の下にある**本物の評価スクリプト（`run_utility_eval.py`、`run_safety_eval.py`、`run_harmbench_eval.py`）を Python サブプロセス経由で起動する仕組み**に統合しました。
  - これにより、`lm-evaluation-harness` による本格的な一般性能評価、および `Llama-Guard-3-8B` を Judge とする本格的な ASR 安全性測定（AdvBench & HarmBench OOD）が実行されます。

### F. 一括実行自動化マスタースクリプトの作成
- **[NEW] [run_all_experiments_suite.sh](file:///mnt/nas/home/hiromi/src/sst_v2/v2/run_all_experiments_suite.sh)**:
  - 実験開始前に `download_llama2_resources.py` を実行し、モデルとデータセットを自動取得。
  - さらに外部公式リポジトリ `SafeMERGE` を自動的に `third_party/SafeMERGE` 配下にクローン・配置するステップを追加しました。
  - 全マージと評価のスイープ処理を自動化し、すべての標準出力は `logs/experiment_run_[TIMESTAMP].log` にリダイレクト保存されます（kiro ログ保存ルールの遵守）。

---

## 2. 実行手順

マージ実験および評価を開始するには、ターミナルで以下のコマンドを実行してください。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/v2
bash run_all_experiments_suite.sh
```

### 実行の流れ
1. **モデルとデータセットのダウンロード**が実行されます (ゲート付きモデルのため `HF_TOKEN` が設定されている必要があります)。
2. **`third_party/SafeMERGE` の自動クローン**が実行されます。
3. **Steering Hook の自動ユニットテスト**が走り、フック検証がパスすることを確認します。
4. **モデルマージ**がストリーミングで順次実行され、`models/merged/` に出力されます。
5. **ベンチマーク評価**が順次呼び出され、`results/raw/` に本物の評価結果が蓄積されます。
