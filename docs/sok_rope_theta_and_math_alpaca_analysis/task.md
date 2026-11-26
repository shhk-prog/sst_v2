# タスクリスト: `rope_theta` 因果切り分け正式比較表 ＆ 新 GSM8K（Alpaca-CoT）× 安全性 最終集計・プロット・ブートストラップ解析

## 完了済みタスク
- [x] `v5/scripts/summarize_rope_theta_ablation.py` を作成・修正し、`v3` (`rope_theta=10,000`) vs `v5` (`rope_theta=1,000,000`) の Before/After 正式比較表（HarmBench / WildGuard / StrongREJECT・拡張 VRR・文字化け率・HumanEval / MBPP）を生成
  - 出力: `v5/outputs/sok_audit/rope_theta_ablation_summary.md` / `.json`
- [x] `v5/scripts/analyze_math_alpaca_cot.py` を作成し、完了済みモデル（現時点 `117/138`、`seed 44` 完了後に同一コマンドで `138/138` へ自動更新可能）の最終集計・妥当性制約付き Pareto フロンティア抽出・3 分類器別安全性–有用性曲線プロット・プロンプト単位ブートストラップ（1,000 回、同一名目 α および同等安全性水準の両方）を実行
  - 出力: `v5/outputs/sok_math_alpaca/math_alpaca_analysis.md` / `.json`
  - 出力図: `math_alpaca_p5_curve_3classifiers.png` / `math_alpaca_all11_pareto.png` / `math_prompt_before_after_alpha06.png`
- [x] 生成画像 3 枚を目視確認し、タイトル–凡例重なり・Pareto ラベルのはみ出しを修正して再生成・再確認
- [x] `v5/tests/test_math_alpaca_cot.py` に集計・Pareto 抽出・pass@1 抽出の単体テストを追加し、`pytest v5/tests` 全 61 件 PASS・NFR2（`v3/`・`v1/`・`v2/` 非改変）を確認

## 残タスク（`seed 44` 完了後）
- [ ] `iag-03` GPU 1 の `seed 44` 残モデル（約 21 本、完了予定 ~16:30–17:00）完了後に `analyze_math_alpaca_cot.py` を 1 回再実行し、全 138/138 モデル (`n=3`) の最終版へ更新する
