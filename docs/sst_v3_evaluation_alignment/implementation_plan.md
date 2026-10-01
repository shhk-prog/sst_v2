# 実装計画: インストラクション訓練データセットによる直接評価の統合

## 目的
`Evol-Instruct-Code-80k` と `MedAlpaca (medical_flashcards)` の2つの特化ドメイン用インストラクションデータセットについて、代理のベンチマーク（HumanEval/MBPP/PubMedQA）に加えて、データセット自体を用いた直接的な能力保持率の評価（Evaluation）を評価パイプラインに追加します。

## 懸念点と対応案
*   **データリークの回避**: 
    FIM（良性テキスト抽出）の訓練・検証でこれらのデータセットの先頭1000サンプルを使用しています。評価時の不当な高スコア（過学習の測定）を防ぐため、評価用サンプルはインデックス1000以降（1000〜1100など）から重複しないように抽出します。
*   **評価手法の設計**:
    指示データセットには標準の選択肢判定などの評価器がないため、以下の2つの指標を組み合わせて独自に算出します。
    1.  **Perplexity (PPL)**: プロンプト（Instruction + Input）を与えた際の、正解出力（Output）に対する予測ロス（CrossEntropy）から算出。
    2.  **Sequence Similarity Score**: 貪欲法（greedy decoding）で応答をテキスト生成させ、正解テキストとの編集距離類似度（0.0〜1.0）を算出。

## 提案する変更内容

### 1. 新規作成: [eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_instruction_datasets.py)
*   指定されたデータセット（`evol_code` または `medalpaca`）のインデックス1000以降から制限件数分を読み込む。
*   モデルを読み込み、ターゲット文のPerplexityおよび生成応答の類似度スコアを算出して結果を保存。

### 2. 修正: [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
*   各モデル（ベース、各マージモデル）の評価ループの中に、`eval_instruction_datasets.py` の呼び出しを追加。
*   結果は別個のJSONファイル（`{model_name}_inst_{dataset}.json`）として独立して保存。

### 3. 修正: [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)
*   パレートフロンティア分析のロード処理にて、`_inst_evol_code.json` および `_inst_medalpaca.json` を検出し、`similarity_score` を `utility` スコアとして取り込むように拡張。

## 検証計画
### 手動テスト
プロジェクトディレクトリでテスト実行を行い、JSONファイルが正しく生成・出力されることを確認する。
```bash
python scripts/eval_instruction_datasets.py --model_path meta-llama/Llama-2-7b-hf --dataset evol_code --output_file results/raw/test_base_inst_evol_code.json --limit 5
```
