# タスクリスト: SST-Merge 実験再計画（ゼロベース・トップ会議向け）

- `[x]` **フェーズ1: 環境構築とデータ準備**
  - `[x]` 実験環境用ディレクトリ (v2_experiments) および README の作成
  - `[x]` Python要件定義 (requirements.txt) の作成
  - `[x]` ベースモデル (Llama-3-8B-Instruct, Mistral-7B-Instruct-v0.3) の準備 (スクリプト引数化)
  - `[x]` 評価環境・マージツールのセットアップスクリプト作成 (setup_env.sh)
  - `[x]` 金融データセット・攻撃データセットの前処理スクリプト作成 (prepare_datasets.py)
  - `[x]` ユーザーによる実際のスクリプト実行（データダウンロード等）
  - `[x]` XSTestデータセットの前処理

- `[/]` **フェーズ2: モデル学習 (Fine-Tuning)**
  - `[x]` Utility FT と Safety FT、および混合データのMixed FT（LR等の条件変更含む）実行スクリプトの作成
  - `[ ]` 金融データを用いた Utility FT ($\theta_{util}$) の実行 (4,500件)
  - `[ ]` Magicoderデータを用いた Coding FT ($\theta_{code}$) の実行 (4,500件)
  - `[ ]` AdvBench+TrustLLMを用いた Safety FT ($\theta_{safe}$) の実行 (~2,000件)
  - `[/]` 作成したモデルの評価（utility, safety）
    - `[x]` 評価スクリプトのエラー修正 (`results*.json` 検索ロジック等)
    - `[x]` コーディング評価のエラー修正 (`HF_ALLOW_CODE_EVAL`)
    - `[ ]` ID (In-Domain) 評価の実行
    - `[ ]` OOD (Out-Of-Domain) 評価の実行

- `[ ]` **フェーズ3: マージ実行 (Mergekit / 公式実装利用)**
  - `[ ]` FIM計算 (Utility FIM, Safety FIM) の実行（サンプルサイズ100）
  - `[ ]` SST-Merge (Full, Diagonal, Data-Free) の各$\alpha, k$スイープマージ
  - `[ ]` Task Arithmetic, TIES, DARE の Mergekit経由でのマージ
  - `[ ]` SafeMERGE, AlignMerge, FWA等の公式実装によるマージ

- `[/]` **フェーズ4: 大規模評価**
  - `[ ]` **Utility評価 (ID/OOD)**:
    - `[ ]` ID: finance-alpaca, Magicoder (eval split) の ROUGE-L 測定
    - `[ ]` OOD: MMLU (Finance領域), HumanEval, MBPP, GSM8K の実行
    - `[ ]` General OOD: ARC-Challenge, HellaSwag の実行による忘却度測定
  - `[ ]` **Safety評価 (ID/OOD)**:
    - `[ ]` ID: AdvBench / TrustLLM ASR の測定
    - `[ ]` OOD: HarmBench ASR の測定
    - `[ ]` Over-refusal: XSTest での False Positive 率測定 (`run_safety_eval.py` 拡張)
  - `[ ]` LLM-as-a-Judge: MT-Bench 及び推論崩壊度の採点 (GPT-4o利用)

- `[ ]` **フェーズ5: 結果分析と論文用の可視化**
  - `[ ]` Safety-Utility パレートフロンティアのグラフ作成
  - `[ ]` Surrogate Hierarchy (Data-Free近似) の順位相関分析
  - `[ ]` FIM妥当性検証: 破壊テスト(Prune Top-K)と保護テスト(Modify Bottom-K)の実施
  - `[ ]` 失敗モード分析結果の定量化・可視化
  - `[ ]` FIMサンプルサイズのアブレーション検証
