# 修正内容の確認 (Walkthrough): vLLM GPU メモリ設定の柔軟化

## 概要
`v3/scripts/eval/eval_utility.py` において、vLLM 利用時の `gpu_memory_utilization` パラメータが `0.85` にハードコードされており、GPU メモリ使用可能容量が不十分な場合に起動失敗（`ValueError`）となっていた問題を修正しました。

## 変更点

### 1. スクリプトの改修
- [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py#L55)
  - コマンドライン引数 `--gpu_memory_utilization` を追加。
  - デフォルト値として環境変数 `VLLM_GPU_MEMORY_UTILIZATION` (未設定時は `0.85`) を参照。
  - `VLLM(...)` の初期化引数に `args.gpu_memory_utilization` を渡すように変更。

## 使用方法

今後評価を実行する際、以下のように `--gpu_memory_utilization` または環境変数 `VLLM_GPU_MEMORY_UTILIZATION` で GPU メモリ使用率を調整可能です。

```bash
# コマンドライン引数で 0.50 (50%) に指定する場合
python scripts/eval/eval_utility.py \
  --model_path models/merged/... \
  --config configs/config_main.yaml \
  --tasks mbpp \
  --output_file results/.../utility_code_mbpp.json \
  --limit 320 \
  --batch_size 32 \
  --use_vllm \
  --gpu_memory_utilization 0.50

# 環境変数で指定する場合
export VLLM_GPU_MEMORY_UTILIZATION=0.50
python scripts/eval/eval_utility.py ... --use_vllm
```

## 注意点
- GPU 上で稼働中の他プロセスが不要な場合は、`ps aux` や `nvidia-smi` でプロセス ID を確認し終了させてください。
