# IFEval コード検証・確認計画

## 概要
`sst_v2` リポジトリにおける IFEval (Instruction Following Evaluation) 評価処理および後処理コード (`v3/scripts/eval/eval_utility.py` 等) の実装内容を精査し、その正当性と妥当性を確認・報告する。

## 検証項目
1. **`lm-eval` パラメータと設定の確認**:
   - `google/IFEval` データセットの構成、`generation_kwargs` (do_sample, temperature, max_gen_toks 等)
   - `apply_chat_template` の適用有無とフォールバックテンプレート
2. **後処理ロジック `fix_ifeval_responses` の検証**:
   - 停止タグ (`[END]`, `### Instruction:` 等) の抽出・切断
   - 反復テキスト (Repetition loop) の検出および除去条件
   - `lm_eval.tasks.ifeval.utils` を用いた再評価手順
3. **評価指標の集計手法**:
   - `prompt_level_strict_acc`, `inst_level_strict_acc`
   - `prompt_level_loose_acc`, `inst_level_loose_acc`
4. **出力結果 JSON の構造確認**:
   - `samples` の保持状態とキー名の互換性
