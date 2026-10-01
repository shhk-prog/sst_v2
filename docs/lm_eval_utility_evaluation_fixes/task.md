# タスクリスト (Task List)

- [x] `v3/scripts/eval_utility.py` の修正
  - [x] 環境変数 `HF_ALLOW_CODE_EVAL="1"` の設定を追加
  - [x] JSONシリアライズエラーを解消するための `make_json_serializable` 関数の実装と適用
  - [x] 例外発生時の CLI フォールバック前の GPU メモリ解放 (`del lm_obj`, `gc.collect()`, `torch.cuda.empty_cache()`) の追加
  - [x] `HFLM` 初期化時に `max_length=4096` を指定するよう追加
  - [x] CLI フォールバック時の引数に `max_length=4096` を追加
- [/] 修正内容の検証（エージェント環境エラーのためユーザー側で実施依頼）
  - [/] 数学タスク (`gsm8k,minerva_math500`) を `limit=5` でテスト実行
  - [/] コードタスク (`humaneval,mbpp`) を `limit=5` でテスト実行
  - [/] 一般能力タスク (`mmlu_pro,mmlu,ifeval`) を `limit=5` でテスト実行
- [x] 修正内容のまとめ (Walkthrough の作成)
