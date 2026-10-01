# タスク概要: vLLM 評価スクリプトの GPU メモリ不足エラー修正と設定柔軟化

## 背景
`v3/scripts/eval/eval_utility.py` を実行した際、vLLM の初期化処理において以下の `ValueError` が発生し、評価タスク（mbpp, pubmedqa, medqa_4options 等）が正常に実行できない。

```text
ValueError: Free memory on device cuda:0 (10.82/93.09 GiB) on startup is less than desired GPU memory utilization (0.85, 79.12 GiB). Decrease GPU memory utilization or reduce GPU memory used by other processes.
```

## 目的
1. `v3/scripts/eval/eval_utility.py` の `gpu_memory_utilization` が `0.85` にハードコードされている問題を解消し、コマンドライン引数 `--gpu_memory_utilization` または環境変数から変更可能にする。
2. vLLM 初期化失敗時のフォールバック処理および引数の柔軟性を向上させる。
3. GPU メモリ空き容量に応じた柔軟な評価実行を可能にする。

## タスク一覧
- [x] `v3/scripts/eval/eval_utility.py` に `--gpu_memory_utilization` 引数を追加
- [x] `VLLM` クラスの初期化時に引数指定された `gpu_memory_utilization` を使用するように修正
- [x] ドキュメント (`docs/vllm_gpu_memory_fix/`) の整備
