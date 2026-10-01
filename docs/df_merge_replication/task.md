# df-merge 再現実験 タスクリスト

- `[x]` 仮想環境の作成とセットアップ (ユーザー様作業)
  - `[x]` `baseline/df-merge/venv_df` の作成
  - `[x]` 依存関係のインストール (`poetry install` または `pip install`)
  - `[x]` `promptsource` のクローンとインストール
- `[x]` 不足データセットのダウンロード (ユーザー様作業)
  - `[x]` `download_dataset.py` の実行 (story_cloze はGatedのためスキップし、既存の5データセットで進めることに決定)
  - `[x]` データセットの配置確認 (paws, qasc, quartz, wiki_qa, winogrande が配置済みであることを確認)
- `[x]` 各タスクモデルのファインチューニング (ユーザー様作業)
  - `[x]` `src/finetune.py` の実行 (5つのデータセット対象、バックグラウンド)
  - `[x]` ログ監視とファインチューンチェックポイントの保存確認
- `[x]` DF-Mergeの実行と評価 (ユーザー様作業)
  - `[x]` `src/df-merge.py` の実行
  - `[x]` 評価結果 (`metrics.json`) の出力確認
- `[x]` 結果の検証とレポーティング (エージェント作業)
  - `[x]` `metrics.json` の解析
  - `[x]` `walkthrough.md` の作成
