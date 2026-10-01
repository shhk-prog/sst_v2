# 実装計画: lm-eval / evaluate の並列実行時キャッシュ競合防止

## 1. 概要
`lm_eval.simple_evaluate` 呼び出し時、Hugging Face `evaluate` モジュールが共通のローカルキャッシュファイルを使用するため、複数プロセスで並列評価が走るとファイルロック競合が発生します。
プロセスごとにユニークな `HF_EVALUATE_EXPERIMENT_ID` を自動設定し、リトライ時にランダムジッターを加えることで競合を根本解決します。

## 2. ユーザー確認が必要な事項
特になし。環境変数の自動補正とランダム待機時間の導入のみのため、既存動作に影響を与えません。

## 3. 開放された質問 / 不確実性
なし。

## 4. 変更予定内容

### [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)

#### [MODIFY] [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
1. スクリプト起動時に `uuid` を用いて `os.environ["HF_EVALUATE_EXPERIMENT_ID"]` を初期化。
2. `simple_evaluate` の例外処理にて、競合エラー発生時に `HF_EVALUATE_EXPERIMENT_ID` を再生成し、`random.uniform(5, 15)` 秒ランダムスリープ後リトライ。

## 5. 検証計画
### 動作確認
- スクリプト単体実行およびコードチェックを行い、エラーなくプロセス ID / UUID 付きの `HF_EVALUATE_EXPERIMENT_ID` が適用されていることを確認。
