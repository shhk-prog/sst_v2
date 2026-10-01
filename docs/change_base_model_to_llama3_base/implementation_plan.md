# 実装計画: ベースモデルを Llama-3-8B に変更

## 目標
Fine-Tuningの実験において、ベースモデルを従来のチャット用モデル（`meta-llama/Meta-Llama-3-8B-Instruct`）からベースの言語モデル（`meta-llama/Meta-Llama-3-8B`）に変更する。これにより、Instructモデル特有の調整がかかっていない生の状態からLoRAファインチューニングやマージの実験を行えるようにする。

## 変更内容
1. **`run_phase2.sh` のモデル指定を修正**
   - `v2/scripts/fine_tuning/run_phase2.sh` の34行目にある `MODEL` 変数の値を `meta-llama/Meta-Llama-3-8B-Instruct` から `meta-llama/Meta-Llama-3-8B` に修正する。

## 確認事項
- `run_phase2.sh` の該当行が正しく書き換わっていることを確認する。
