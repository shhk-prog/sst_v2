# Hirundo / Secure Merge 比較検証実験結果ウォークスルー (計画フェーズ)

本ドキュメントは、Hirundo モデルと Secure Merge モデルの比較検証実験の進捗および最終結果をまとめるウォークスルーです。
現在は計画および設計の段階にあります。

## 実施した内容 (計画フェーズ)
1. **Hirundo モデルの技術調査**:
   - `hirundo-io` が公開している Llama-3.2-3B および Gemma 3/4 の hardened (unlearned) モデルを確認しました。
   - 既存の SST-Merge 実験環境（`v3/`）と適合し、かつマージおよび評価が可能なベースモデル（`meta-llama/Llama-3.2-3B-Instruct` 等）を選定しました。
2. **専用検証スクリプトの設計**:
   - `eval_safety.py` などの既存環境を汚染しないよう、独立した検証用スクリプト `v3/scripts/eval_hirundo_unlearning.py` を定義しました。
3. **ドキュメントの保存**:
   - プロジェクト内の `docs/hirundo_unlearning_analysis/` 配下に実験計画およびタスクリストを作成・保存しました。

---

## 期待される検証の比較軸

実験実行により、以下の4つの主要な比較結果を分析し、Pareto プロット (`results/hirundo_analysis/pareto_frontier.png`) として出力します。

### 1. Hirundo vs Base モデル
- Hirundo の unlearning 適用モデルと元の base モデルで、ASR (Attack Success Rate) の低減率と、一般性能 (Utility) の変化を測定。

### 2. Secure Merge vs Hirundo
- 同一ベースモデルに SST-Merge または他の Secure Merge 手法を適用したモデルと、Hirundo モデルを比較。
- 安全性と性能の Pareto Frontier を描画し、どちらがより優れたトレードオフ（効率的フロンティア）にあるかを明らかにします。

### 3. Hirundo + Guardrail
- Hirundo の重みレベルアンラーニング防御に、WildGuard などのガードレール分類器を組み合わせた場合の相乗効果を評価。

### 4. Hirundo + Secure Merge
- Hirundo の unlearned 重みに対してさらに Secure Merge で安全性を注入する、またはマージした場合の相互作用（効果の打ち消し、あるいは相乗効果、過剰拒否の有無）を評価。
