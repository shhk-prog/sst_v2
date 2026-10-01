# 実装計画: general_ifeval 評価ロジックの修正

## 1. 目的
`general_ifeval` の評価において、モデル本来の指示追従性能を正確に測定できるよう、以下2点の修正を行う。
- **課題1**: Chat Template 未適用による Completion型動作（指示無視・プロンプト書込み）の防止
- **課題2**: 繰り返しテキスト（無限ループ）によるトークン上限溢れ・不必要な失点の防止

---

## 2. 変更内容

### Component: [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py)

#### [MODIFY] [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py)
1. **`parse_args` への引数追加**:
   - `--apply_chat_template`: デフォルト `True` (明示的に `--no_chat_template` 等で無効化も可能)。
2. **`run_lm_eval_python_api` の修正**:
   - `HFLM` 初期化時に `apply_chat_template=args.apply_chat_template` を渡す。
3. **`run_lm_eval_cli_fallback` の修正**:
   - `apply_chat_template` が有効な場合、コマンドライン引数に `--apply_chat_template` を追加する。
4. **`fix_ifeval_responses` 関数の新設**:
   - IFEval のレスポンス (`filtered_resps` / `resps`) から以下のクリーニングを実施：
     - **反復検出・切断 (Repetition Truncation)**: 同じ行または短文が連続して反復（例: 3回以上重複）している場合、最初の出現以降を切り捨てる。
     - **余分な停止タグ・プロンプト再描画タグの除去**: `[END]`, `[DONE]`, `### Instruction:` 等の不要タグ以降を削除。
   - `lm_eval` の IFEval 検証関数 (`test_instruction_following_strict` 等) を使って切り捨て後のテキストを再判定し、`prompt_level_strict_acc` などのスコアを再計算・更新する。

---

## 3. 検証計画

- **評価処理の動作確認**:
  - `eval_utility.py` をデバッグ実行し、`apply_chat_template` が正常に機能すること、および反復ループロジックが応答テキストを正しく整形・切り詰めることを確認する。
