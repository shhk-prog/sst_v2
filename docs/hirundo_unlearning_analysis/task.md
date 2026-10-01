# Hirundo と Secure Merge 比較検証実験タスクリスト

- `[x]` 実験の準備と環境構築
  - `[x]` 比較検証用のベースモデルと Hirundo hardenedモデルの動作確認 (Llama 3.2-3B または Gemma 3-1B)
  - `[x]` 専用設定ファイル `v3/configs/config_hirundo.yaml` の作成
- `[x]` 実装
  - `[x]` 専用検証スクリプト `v3/scripts/eval_hirundo_unlearning.py` の実装
- `[/]` 実験の実行
  - `[ ]` ベースモデルおよび Hirundo hardenedモデルの単体評価 (ASR & Utility)
  - `[ ]` 同一ベースモデルに対する Secure Merge マージモデルの評価
  - `[ ]` 複合ディフェンス評価 (Hirundo + Guardrail / Hirundo + Secure Merge)
- `[ ]` 解析とレポーティング
  - `[ ]` 性能・安全性トレードオフ (Pareto) の解析とグラフプロット生成
  - `[ ]` 実験結果をまとめた `walkthrough.md` の作成と保存
