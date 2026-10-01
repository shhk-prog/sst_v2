# 実装計画: vLLM GPU メモリ使用量の設定柔軟化と評価スクリプト修正

## 1. 概要
`v3/scripts/eval/eval_utility.py` で vLLM を利用する際、GPU メモリ使用率 (`gpu_memory_utilization`) が `0.85` に固定されているため、他のプロセスが GPU を使用している場合や小容量の GPU 環境で `ValueError` が発生します。
これを回避するため、`--gpu_memory_utilization` 引数を追加し、環境変数またはコマンドライン引数で動的に変更できるように修正します。

## 2. ユーザー確認が必要な事項
特になし（既存のデフォルト値 `0.85` は維持するため、後方互換性が保たれます）。

## 3. オープンクエスチョン / 不確実性
- 現在 GPU (`cuda:0`) 上で約 82.27 GiB のメモリを占有している他のプロセスが存在します。評価実行前に不要なプロセスをキルするか、または `--gpu_memory_utilization` を低く設定して実行する必要があります。

## 4. 変更予定内容

### [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)

#### [MODIFY] [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
1. `parse_args()` 関数に `--gpu_memory_utilization` オプションを追加。
   - デフォルト値: `float(os.environ.get("VLLM_GPU_MEMORY_UTILIZATION", 0.85))`
2. `run_lm_eval_python_api()` 関数で `VLLM(...)` の呼び出し時にハードコードされている `gpu_memory_utilization=0.85` を `args.gpu_memory_utilization` に変更。

## 5. 検証計画
### 自動テスト / 動作確認
- `--gpu_memory_utilization 0.4` などのオプションを指定して `v3/scripts/eval/eval_utility.py` の動作およびヘルプ表示を確認。
