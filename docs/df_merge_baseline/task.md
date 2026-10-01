# タスクリスト: df-merge ベースラインの実行

- [ ] 1. 環境構築
  - [ ] `baseline/df-merge` にて `poetry install`
- [ ] 2. データセットとモデルのダウンロード
  - [x] `download_dataset.py` を作成し実行
  - [x] `download_models.py` を作成し実行
  - [ ] `promptsource` パッケージのインストール
- [x] 3. ファインチューニング (FT)
  - [x] `t5-base` を用いた各データセットのファインチューニングの実行
- [x] 4. DF-Merge と評価
  - [x] `src/df-merge.py` の実行 (ei)
  - [x] `src/df-merge.py` の実行 (ucb)
- [x] 5. レポート作成
  - [x] 評価結果をまとめ、walkthrough を作成
