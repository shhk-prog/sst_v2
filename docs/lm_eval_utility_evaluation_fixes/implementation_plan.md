# lm-eval ユーティリティ評価エラーの修正計画（更新）

`lm-eval` を使用して `WizardMath-7B` などのモデルで `mmlu_pro`, `mmlu`, `ifeval` などのタスクを評価する際、以下のエラーが発生して評価が失敗する問題を解決します。

## 追加で発生した問題
- **最大シーケンス長の不一致によるエラー**:
  `mmlu_pro` や `ifeval` などのタスクは、生成最大トークン数 (`max_gen_toks`) に `2048` が要求されます。
  しかし、Llama-2 7B ベースのモデルのデフォルトの最大シーケンス長 (`self.max_length`) は `2048` であるため、入力コンテキスト用のサイズが確保できず（`max_ctx_len = self.max_length - max_gen_toks` = 0 となり）、`lm-eval` 内で `Invalid configuration: requested max tokens to generate (2048) must be less than model's maximum sequence length (2048)` という検証エラーが発生します。

---

## 提案される変更

### ユーティリティ評価スクリプト

#### [MODIFY] [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py)

- **モデル最大シーケンス長の上書き設定**:
  - Python API で `HFLM` インスタンスを作成する際、`max_length=4096` を指定して最大シーケンス長を安全に拡張します。これにより、タスク側で `max_gen_toks=2048` が要求された場合でも検証エラーを回避して実行できるようになります。
  - CLI フォールバック時のコマンド引数にも `--model_args` のオプションとして `max_length=4096` を含めるよう修正します。

---

## 検証計画

### 自動 / 手動テスト
修正したスクリプトが正常に動作するか、以下のコマンドを実行してテストします。

1. **一般能力タスク (`mmlu_pro`, `mmlu`, `ifeval`) のテスト実行**:
   ```bash
   python v3/scripts/eval_utility.py \
     --model_path WizardLMTeam/WizardMath-7B-V1.0 \
     --config v3/configs/config.yaml \
     --tasks mmlu_pro,mmlu,ifeval \
     --output_file results/raw/test_WizardMath_utility_general.json \
     --limit 5
   ```

上記コマンドをユーザー側で実行し、エラーが発生せずに Python API 経由での評価が正常に完了し、結果が JSON 保存されることを確認します。
