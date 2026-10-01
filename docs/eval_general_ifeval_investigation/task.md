# タスク: general_ifeval の評価修正（Chat Template適用 & 反復ループカット）

## 概要
前回調査で判明した `general_ifeval` の評価上の以下2つの主要課題を修正・改善する。
1. **Chat Template (プロンプトフォーマット) の適用**:
   `eval_utility.py` にて `HFLM` に `apply_chat_template=True` を導入し、生プロンプトではなくモデルに応じた対話フォーマットで入力されるようにする。
2. **反復ループカット・後処理関数の実装 (`fix_ifeval_responses`)**:
   `WizardCoder` 等で発生する連続重複テキスト（無限ループ）を検出し、反復が発生した地点でテキストを適切に切り詰め（Truncate）、スコアを再判定する後処理を追加する。

## 実施ステップ
- `eval_utility.py` の引数解析および `HFLM` / CLI 呼び出し部に `--apply_chat_template` オプションを追加。
- IFEval の出力テキストから反復ループや余剰タグを除去する `fix_ifeval_responses` 関数を実装。
- テストおよび挙動確認。
