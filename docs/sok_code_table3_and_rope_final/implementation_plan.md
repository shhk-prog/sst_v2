# 実装計画: 表 3（`safety+code`）・`rope_theta` 比較表 確定集計

## 目的
ロック済み `official_tab_nl` による HumanEval 全 33 本の再評価（`20261126-1518_code-table3-and-rope-humaneval`）完了を受け、未検証の MBPP を除外した確定版の表 3（10 手法 × 3 seed + 単体参照）および `rope_theta` 切り分け比較表を CPU 上で集計・確定する。

## 設計方針
1. **データ整合性と再計算**:
   - 安全性・結合 VRR（`is_gibberish` または拡張文字化け規則のいずれかで崩壊なら無効、下限 `90%`）は `summarize_rope_theta_ablation.py` の `eval_safety_dir` をそのまま再利用し、先行集計と定義を完全に一致させる。
   - コード有用性はロック済み `official_tab_nl`（HumanEval 全 164 問）のみを採用し、未検証 MBPP および Code Avg 列を除外する。
   - 文章中の数値もすべて集計オブジェクトから動的に埋め込み、表と本文の数値乖離を防ぐ。
2. **非破壊・トレーサビリティ（指示書 v2 §1）**:
   - 新ランフォルダ `20261126-1740_code-table3-and-rope-summary-final` に Markdown / JSON / `summary.json` を出力。
   - 旧 `20261126-1344_rope-theta-ablation-summary` は削除・上書きせず `RUN.md` と `INDEX.md` で「置き換え済み」に更新する。
3. **検証**:
   - `v5/tests/test_summarize_code_table3_and_rope_final.py` で「暫定」および MBPP 数値列が残存しないこと・LED-Merging† が全 3 seed で `2.44%` に一致すること・TA `rope_theta` が `4/164 → 7/164` であることを自動検証する。
