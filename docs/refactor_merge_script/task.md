# リファクタリング タスクリスト: `v3/scripts/merge.py`

- [x] 新規パッケージ `v3/scripts/mergers/` の作成
  - [x] `constants.py`: 定数・マッピング等の分離
  - [x] `utils.py`: モデル操作・テンソルユーティリティ・構造設定関数の分離
  - [x] `fim.py`: FIM推定・キャッシュ処理の分離
  - [x] `sst.py`: Proposed SSTマージ処理 (`merge_sst`) の分離
  - [x] `mergekit.py`: Mergekit連携処理 (`run_mergekit`) の分離
  - [x] `baselines.py`: 外部ベースライン処理 (`safemerge`, `mergealign`, `led_merging`, `matena_fisher`) の分離
  - [x] `__init__.py`: パッケージエクスポートの定義
- [x] `v3/scripts/merge.py` のリファクタリング (エントリポイント化)
- [x] 動作確認・検証
  - [x] 全モジュールの構造およびインポート整合性の確認
