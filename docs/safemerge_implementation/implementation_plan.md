# SafeMERGE 実装計画

## 目的
arXiv論文「SafeMERGE: Preserving Safety Alignment in Fine-Tuned Large Language Models via Selective Layer-Wise Model Merging (2503.17239)」の手法を再現するため、論文と全く同じデータセット、モデルでのファインチューニング(FT)、評価方法を追加し、`SafeMERGE.sh` として実行可能なスクリプトを作成します。

## ユーザーへの確認事項 (User Review Required)
> [!IMPORTANT]
> - **対象モデル**: 論文では `Llama-2-7B-Chat`, `Llama-3.1-8B-Instruct`, `Qwen-2-7B-Instruct`, `Qwen-2.5-7B-Instruct` が使用されています。今回の `SafeMERGE.sh` ではデフォルトを `meta-llama/Meta-Llama-3.1-8B-Instruct` とし、ベースモデルとして `meta-llama/Meta-Llama-3.1-8B` を使用する設定で進めますが、よろしいでしょうか？（引数等で変更可能な作りとします）
> - **評価環境**: 論文と同じく、Llama-Guard-3-8Bを用いた DirectHarm, HexPhi の評価、および GSM8K, PubMedQA の Utility 評価を実装します。実行時間が長くなる可能性がありますが、テスト用にサンプリング数などを調整できるようにパラメータ化します。

## 提案する変更内容

### 1. データセットの追加 (Data Preparation)
論文で使用されている以下のデータセットを取得・整形するスクリプトを追加します。
- **Utility (FT & Eval)**: `GSM8K` (算数推論), `PubMedQA` (医療質問応答)
- **Safety (FT)**: `SafeInstruct` (またはBianchi et al.の安全性データセット)
- **Safety (Eval)**: `DirectHarm`, `HexPhi` (Red-teaming用データセット)

### 2. スクリプトの追加・修正 (Scripts)

#### [NEW] `v2/scripts/fine_tuning/prepare_safemerge_data.py`
上記のデータセットをダウンロードし、既存のFTスクリプト (`run_lora_ft.py`) で読み込める JSON 形式に変換する処理を実装します。

#### [NEW] `v2/third_party/SafeMERGE` (GitHubリポジトリのクローン)
ユーザーの要望に従い、独自の `run_safemerge.py` を作成するのではなく、公式リポジトリ `aladinD/SafeMERGE` をそのまま利用します。
- `v2/third_party/SafeMERGE` ディレクトリにリポジトリをクローンまたはダウンロードします。
- 公式の `get_safemerge_model.py` および `utils.py` を用いて、コアアルゴリズム（射影行列の計算およびコサイン類似度に基づく閾値判定とマージ処理）を実行します。
- マージスクリプト内で公式の処理をインポートして呼び出すか、ラッパースクリプトから必要な引数（`--base_model_id`, `--finetuned_model_id`, `--safety_model_id` など）を渡してマージを実行します。

#### [NEW] `v2/scripts/fine_tuning/SafeMERGE.sh`
`run_phase2.sh` に似たスクリプトを作成します。
1. データ準備 (`prepare_safemerge_data.py`)
2. Safe Model の FT (SafeInstructデータを使用)
3. Utility Model の FT (GSM8K または PubMedQA を使用)
4. 公式コード (`v2/third_party/SafeMERGE/get_safemerge_model.py`) を用いたマージ処理
5. 評価スクリプト群（GSM8K/PubMedQA, DirectHarm/HexPhi, IFEval等）の実行

### 3. 評価指標の実装 (Evaluation)
- Utility: `lm-eval` を用いて GSM8K の Exact Match や PubMedQA, MMLU の精度を測定できるよう連携します。
- Safety: `run_safety_eval.py` を拡張または新規作成し、DirectHarm および HexPhi のプロンプトに対して `Llama-Guard-3-8B` を用いた判定を行います。

## 検証計画 (Verification Plan)
1. **動作確認**: `SafeMERGE.sh` を少epoch・少サンプル設定で実行し、データ準備から評価まで一通りエラーなく完了することを確認する。
2. **ログ確認**: 公式の `get_safemerge_model.py` が正常に動作し、指定されたベースモデルとLoRAアダプタを用いて正しくマージ処理が行われているかログで確認する。
3. **結果出力**: GSM8Kの精度およびDirectHarmのASRなどの結果がJSONファイル等に出力されることを確認する。
