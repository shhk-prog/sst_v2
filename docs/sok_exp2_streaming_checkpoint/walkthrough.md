# 修正内容の確認 (Walkthrough): SoK 実証 2 全フェーズの 1 件ずつ逐次保存・途中再開対応

## 変更サマリー
`v3/` を一切改変せず（NFR2 厳守）、`v5/scripts/` 配下に 1 件ずつ逐次保存・途中再開対応のラッパー 3 本を新規作成し、`slurm_fp32_sst_math.sh` をそれらに切り替えた。

| フェーズ | 改修前（`v3` 直接呼び出し） | 改修後（`v5` 逐次保存版） | 保存先・再開挙動 |
|:---|:---|:---|:---|
| **マージ** | 1 α モデルごと保存（metadata は非原子） | [merge_fp32_sst_math.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/merge_fp32_sst_math.py): 1 α ごと保存＋`merge_metadata.json` 原子保存（`fsync` + `os.replace`） | 完了済み α は自動スキップ |
| **安全性評価（生成・分類）** | `--use_vllm` 生成は **320 件一括保存**（分類のみ 1 件ごと） | [eval_safety_streaming.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_safety_streaming.py): 生成・分類とも **1 件ごとに原子保存** | `*_safety.json` を 1 件ごとに更新。再実行時は `response is None` / `asr is None` の未完了分から即再開 |
| **Math 有用性評価** | **640 件（GSM8K+Minerva500）終了後に 1 回保存** | [eval_utility_streaming.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/eval_utility_streaming.py): 1 件推論するごとに `.stream.jsonl` へ 1 行追記＋`fsync` | `*_utility_math.json.stream.jsonl` から完了済み件数を復元し、未推論の次の 1 件から再開 |
| **HarmBench 再分類** | **全ファイル・全件（最大 7,680 件）推論後に一括保存** | [reclassify_harmbench_streaming.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/scripts/reclassify_harmbench_streaming.py): **1 件ごとに原子保存** | `*_safety.json` を 1 件ごとに更新（全件完了時のみトップレベル確定） |

## 検証結果
- `bash -n v5/scripts/slurm_fp32_sst_math.sh` / `py_compile`: 全ファイル正常
- `pytest v5/tests -q`: 新規 [test_streaming_eval.py](file:///mnt/nas/home/hiromi/src/sst_v2/v5/tests/test_streaming_eval.py)（途中クラッシュ・破損末尾行からの再開・部分保存テスト 3 件）を含め全テスト合格
- `git status --short -- v3/scripts v3/results v1 v2`: 変更ゼロ（NFR2 維持）
