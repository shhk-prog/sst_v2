# 安全性個別評価・公式判定および実用性ドメイン評価拡張のウォークスルー

本作業において、安全性評価ベンチマークの独立評価・公式判定モデルの導入、および実用性評価（Utility）における各ドメイン（Math/Code/Medical）公式評価タスクの追加統合が完了いたしました。

## 実施した変更内容

### 1. 安全性評価（Safety）の個別評価および公式判定の導入
各安全性ベンチマーク（HarmBench, JailbreakBench, StrongREJECT, WildJailbreak）について、従来の簡易キーワード拒否判定を廃止し、それぞれのベンチマークが公式に指定・確立している独自の評価モデルをローカルでロードして判定するロジックを導入しました。

*   **[eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py)**:
    - 評価対象モデルの推論（応答生成）完了後、メモリリークや VRAM 競合を防ぐために VRAM キャッシュを完全にクリア（`del model; gc.collect(); torch.cuda.empty_cache()`）した上で、各ベンチマークの公式判定器をロードして実行する仕組みにアップグレードしました。
    - **HarmBench**: 公式判定モデル **`cais/HarmBench-Llama-2-13b-cls`** を使用して判定（`Yes` / `No`）。
    - **JailbreakBench / WildJailbreak**: 安全判定モデル **`allenai/wildguard`** を使用して判定。
    - **StrongREJECT**: クローンした `strong_reject` 公式パッケージによる判定（実数スコア 0〜1）。

*   **[data_prep.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/data_prep.py)**:
    - 安全性データセットの個別準備および、3つの公式リポジトリ（`strong_reject`, `HarmBench`, `jailbreakbench`）を自動で `evaluators/` ディレクトリ配下に `git clone` して editable モード（`pip install -e`）でインストールするロジックを追加しました。
    - WizardMath および Medalpaca の FIM 構築用データセットロードも、Hugging Face Hub 上で確実にアクセス可能な `gsm8k` および `medalpaca/medical_meadow_medical_flashcards` を参照するように修正しました。

*   **[run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)**:
    - 安全性評価実行ループを `safety_tasks` ごとに回し、結果を `{model}_{task}_safety.json` として個別に保存するように拡張しました。

*   **[pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)**:
    - 複数の安全性 JSON をタスクごとにパースし、各ベンチマーク別（および全タスク平均: `average`）に個別のパレート曲線（`pareto_frontier_{task}.png`）およびサマリー（`pareto_metrics_summary_{task}.csv`）を生成する処理に拡張しました。

### 2. 有用性評価（Utility）へのドメイン別公式評価タスクの統合
各ドメインモデル（Math, Code, Medical）の FT（ファインチューニング）で公式に使用されている評価ベンチマークと完全に同等の評価を実用性評価に組み込みました。

*   **[config.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v3/configs/config.yaml#L28)**:
    - 実用性評価タスク (`utility_tasks`) に、Math特化の **`gsm8k`**, **`math_500`**、Code特化 of **`openai_humaneval`**, **`mbpp`**、Medical特化の **`pubmedqa`**, **`medqa_us`** を追加・統合しました。
*   **[pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py#L31)**:
    - コード生成メトリクスである `pass` (HumanEval の `pass@1` など) をパーサーが正しく識別し、実用性スコアに正常に組み込めるように抽出ルールを拡張しました。

## 検証結果
- `data_prep.py` を実行し、データセットが `data/eval/eval_harmful_{task}.json` に個別保存されること、および `evaluators/` 内に公式リポジトリが自動でクローン・インストールされることを検証・確認しました。
- 安全性推論終了後の GPU キャッシュクリアと公式判定器のロードが正常に動作し、個別に結果が保存されることを確認しました。
