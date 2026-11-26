# タスクリスト: Day 1（数学評価修復・SafeMERGE H3 監査・rope_theta 準備・MergeBench 確認）

- [x] `WizardMath-7B-V1.0` の GSM8K 6.25% 崩壊の原因特定（`### Response:\n` に CoT トリガ `"Let's think step by step."` と Alpaca 接頭辞が欠落）
- [x] WizardMath 公式 Alpaca-CoT プロンプトによる 1 件逐次保存 GSM8K 評価スクリプト `v5/scripts/eval_math_alpaca_cot.py` とランチャー `v5/scripts/run_math_alpaca_reeval.sh` の作成
- [x] `MergeBench` 全 40 リポジトリの HuggingFace API 実在・公開確認およびローカルキャッシュ確認
- [x] P4 因果切り分け用 `rope_theta=1,000,000` ゼロコピーモデル（3 手法）の作成と実行スクリプト `v5/scripts/run_rope_theta_ablation.sh` の整備
- [x] `SafeMERGE` 更新層数・重み差分（5.7 節 H3）の CPU 監査完了
- [x] 単体テスト追加（`v5/tests/test_math_alpaca_cot.py`）および全 60 件合格確認
- [x] `walkthrough.md` の記録と `iag-02` 実行コマンドの提示
