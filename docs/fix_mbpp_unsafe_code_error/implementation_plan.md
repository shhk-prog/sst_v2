# 実装計画：mbppタスク評価における `confirm_run_unsafe_code` エラー解消

`run_eval_coding.sh` において `mbpp` タスクを実行する際、`lm-evaluation-harness` が安全性の制限によって実行を拒否するエラー（ValueError）を解消するための実装計画です。

## エラーの背景と原因

ログを詳細に調査したところ、以下のエラーが発生してパイプラインが停止していました：
1. **Unsafeエラー**:
   ```
   ValueError: Attempted to run task: mbpp which is marked as unsafe. Set confirm_run_unsafe_code=True to run this task.
   ```
2. **環境変数エラー**:
   単体実行時に `HF_ALLOW_CODE_EVAL` 環境変数が設定されていないため、以下のコード評価警告エラーが発生していました：
   ```
   ValueError: The "code_eval" metric executes untrusted model-generated code in Python. ... set the environment variable HF_ALLOW_CODE_EVAL="1".
   ```

---

## 提案する変更内容

### [utility_FT]

#### [MODIFY] [run_eval_coding.sh](file:///mnt/nas/home/hiromi/src/sst_v2/utility_FT/run_eval_coding.sh)

`lm_eval` 実行引数に `--confirm_run_unsafe_code` を追加し、スクリプトの冒頭で `HF_ALLOW_CODE_EVAL=1` を export します。

```diff
+# コード評価(mbpp)のためのフラグ設定
+export HF_ALLOW_CODE_EVAL=1
+
 mkdir -p "$OUT_DIR"
```

```diff
 lm_eval \
     --model hf \
     ${PEFT_LM_EVAL:---model_args pretrained=${MODEL_NAME},trust_remote_code=True} \
     --tasks mbpp \
     --batch_size 1 \
+    --confirm_run_unsafe_code \
     --output_path "${OUT_DIR}/coding_metrics.json"
```

---

## 検証計画

1. **修正の適用**: `run_eval_coding.sh` に引数と環境変数を追加します。
2. **単体テストの実行**:
   ユーザー様にターミナルにて、以下のコマンドを実行していただき、`mbpp` 評価がエラーなく実行・完了することを確認します：
   ```bash
   cd /mnt/nas/home/hiromi/src/sst_v2/utility_FT
   ./run_eval_coding.sh
   ```
   * **期待される結果**:
     * エラー（ValueError）が発生せず、`mbpp` の評価が実行され、結果が `../results/BaseModel/coding_metrics.json` に正常に保存されること。
