# Llama-2-7B 3特化モデルに対する SST-Merge 実験計画 (kiro 仕様遵守版)

本計画は、ユーザーより追加指示された **`/mnt/nas/home/hiromi/src/sst_v2/v2/kiro` 仕様の完全な遵守** に基づき、4パターンのマージ組み合わせと12種の手法、各種評価ベンチマーク、およびアブレーションスタディを実行するための実験フレームワーク構築を定義します。

---

## 1. kiro 仕様の遵守方針

本実験は、`kiro/steering/` の常時適用ルールおよび `kiro/specs/sst-merge-aaai27/` の要件を以下の通り徹底して遵守します。

### A. 比較手法のカスタム実装コード排除（RuntimeError強制）
- Task Arithmetic, TIES, DARE などの標準手法については、独自に Python 等で再実装したカスタムマージロジックは一切使用せず、公式 `mergekit` を用います。
- スクリプト実行時に `mergekit` が検出できない場合は、フォールバックせず即座に `RuntimeError` を送出して終了します。

### B. 実験管理の YAML 化の強制
- 実験のすべてのパラメータ（モデル、データセット、乱数シード、$\alpha$ および $k$ のスイープ設定）は、`configs/aaai27/llama2_sst_experiment.yaml` 設定ファイルに完全に記述し、コード内にパラメータをハードコーディングすることを禁止します。

### C. 再現性とメタデータの完全保存
- 乱数シードは必ず固定（`seed=42` を含む3シード）して実行します。
- マージ後モデルのディレクトリには、モデル構成、学習設定、手法名、実行時の Git commit hash、完全な実行コマンドを含む `merge_metadata.json` を同梱し、さらにプロジェクトルートの `metadata/` ディレクトリにも同一ファイルをバックアップします。

### D. Data-Free 実験における I/O およびキャッシュ統計遮断
- `data_free_sst` メソッドの実行時には、`steering_hook` による `builtins.open` の監視と I/O 遮断を有効化し、`v2/data` 配下の実データセットや、過去に計算した FIM キャッシュ等の「データ由来統計」へのアクセスを一切遮断します。

### E. archiveコード (`v1/`) の使用禁止
- 旧カスタムマージスクリプトなど、`v1/` ディレクトリ配下にあるレガシーモジュールのインポートや参照を厳格に禁止します。

---

## 2. 実験構成

### 2.1 マージパターン (4パターン)
- **Math + Code** (WizardMath-7B-V1.0 + WizardCoder-7B-V1.0)
- **Math + Medical** (WizardMath-7B-V1.0 + Medalpaca-7B)
- **Code + Medical** (WizardCoder-7B-V1.0 + Medalpaca-7B)
- **Math + Code + Medical** (3モデル同時マージ)

### 2.2 評価手法 (Methods)
- `mergekit` を用いて実行する手法: Task Arithmetic, TIES, DARE, DELLA
- 独自実装する手法: Fisher-weighted averaging, MergeAlign, SafeMERGE, LED-Merging, SST-Merge, Data-Free SST-Merge

### 2.3 アブレーション項目
- **SST ratio**: `Fh/Fb`, `Fh only`, `1/Fb only`, `magnitude`, `random`
- **Variants**: `additive`, `interpolation`, `hard mask`, `soft mask`, `layer-wise on/off`, `FIM sample size N`, `data-free proxy`

---

## Proposed Changes

### 1. フックとテストの修正
#### [MODIFY] [steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/steering_hook.py)
- ベースモデルのチェックにおいて `Llama-2-7B` および `WizardMath`, `WizardCoder`, `medalpaca` などの関連キーワードを検証許可リストに追加します。
#### [MODIFY] [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/test_steering_hook.py)
- テストケースにおいて `Llama-2-7B` を許可するテストを追加し、ユニットテスト全体がパスすることを確認します。

### 2. 実験 YAML ファイルの作成
#### [NEW] [llama2_sst_experiment.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v2/configs/aaai27/llama2_sst_experiment.yaml)
- Llama-2-7B 特化モデル用の一括マージ設定（モデルパス、データセット、アブレーションスイープ等）を定義します。

### 3. ストリーミング・マージスイートの作成
#### [NEW] [merge_llama2_sst_suite.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/merge/merge_llama2_sst_suite.py)
- メモリ効率を最大化するため、`safetensors` のテンソル単位で逐次ロードし、GEVP / FIM比 / FWA などの計算を行ってから書き出すストリーミングマージエンジン。
- `mergekit` 呼び出し時は、自動的に YAML 設定を生成して `mergekit-yaml` CLI をサブプロセスで実行し、エラー時は `RuntimeError` を強制します。
- `merge_metadata.json` を指定のディレクトリへ同時保存する機能を実装します。

### 4. 評価および自動実行スクリプトの整備
#### [NEW] [eval_llama2_suite.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/evaluation/eval_llama2_suite.py)
- `lm-evaluation-harness` の API をパースし、MMLU, GSM8K, MATH-500, MBPP, IFEval 評価を一元管理するスクリプト。
- Safety評価のASR簡易算出パイプライン。

---

## Verification Plan

### Automated Tests
1. `python v2/scripts/test_steering_hook.py` を実行し、フックの挙動が期待通りであることを検証。
2. ダミーの重みを用いて `merge_llama2_sst_suite.py` の動作検証（`mergekit` 呼び出しおよび独自マージのドライラン）。
3. テストモデルを用いた推論実行の確認。
