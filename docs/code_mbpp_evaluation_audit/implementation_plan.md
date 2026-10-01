# code_mbpp 評価プロセスの修正・改善計画 (Implementation Plan)

`code_mbpp`（MBPPベンチマーク）における評価スコアが正常に算出されていない問題の調査結果と修正方針をまとめます。

---

## 1. 調査結果 (調査概要)

### 問題の現象
- `v3/results/debug_limit320` 等に保存されている MBPP の評価結果において、Code専用モデルである `WizardCoder-Python-7B-V1.0` を含むすべてのモデルで `pass_at_1` スコアがほぼ `0.0` (0%) と記録されている。

### 原因の特定
1. **ストップシーケンス未指定による `[END]` タグの残存**:
   - `lm-eval` の標準 `mbpp` 設定 (`mbpp.yaml`) では、プロンプトの最後に `[BEGIN]\n` が付与される。
   - モデルは回答生成完了時に `[END]` という終了タグを出力するが、`lm-eval` の `generation_kwargs.until` に `"[DONE]"` しか登録されていないため、`[END]` タグが切り取られずにレスポンス文字列に残ってしまう。
2. **Python 構文エラー (`SyntaxError`) の発生**:
   - 評価フェーズにおいて、生成コードの末尾に `[END]` が付いた状態で `exec()` によりテストコードと結合・実行される。
   - `[END]` は Python の正しい文法ではないため、即座に `SyntaxError` となり、本来正解しているロジックであってもすべて不合格（Pass@1 = 0）と処理されていた。

---

## 2. 影響範囲

- `v3/scripts/eval_utility.py` を用いて実行されたすべての `mbpp` / `code_mbpp` 評価実験。
- 今までのベンチマーク評価で MBPP スコアが不当に低下していた可能性がある。

---

## 3. 提案する修正案

### 修正案 1: `eval_utility.py` への MBPP 出力クリーンアップ処理の追加 (`fix_mbpp_responses`)
HumanEval のインデント補正 (`fix_humaneval_indentation`) と同様に、MBPP の生成結果に対しても後処理クリーンアップを追加する。

具体例:
- `[END]` タグの除去
- `[BEGIN]` タグや Markdown のコードブロック (```python ... ```) の抽出
- 末尾の余計な解説文やテストプリントの除去

### 修正案 2: `lm_eval` 呼び出し時のストップシーケンス設定の最適化
`lm_eval` の `generation_kwargs` またはタスクカスタマイズにおいて、`until: ["[DONE]", "[END]", "\n\n\n", "```"]` を指定し、生成段階で余分なタグを出力させないようにする。

---

## 4. 検証計画

### 1) サンプル修正スクリプトの作成と既存 JSON ログの修正テスト
- 既存の `sst_merge_v3_main_base_WizardCoder_utility_code_mbpp.json` などのレスポンスから `[END]` を除去し、`lm_eval` または `pass_at_k` の評価関数を適用した際にスコアが正常（本質的な Pass@1）に回復するか試算・検証する。

### 2) 実際の修正結果の確認
- クリーンアップ後のスコアが WizardCoder 等の期待値 (約 50-60% 前後) に戻るか確認する。
