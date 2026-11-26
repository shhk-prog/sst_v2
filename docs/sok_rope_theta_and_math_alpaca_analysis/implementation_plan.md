# 実装計画: `rope_theta` 因果切り分け正式比較表 ＆ 新 GSM8K（Alpaca-CoT）× 安全性 最終集計パイプライン

## 1. 背景と目的
ASIACCS 2027 SoK 論文（草稿 `v5/docs/【草稿】SoK: 安全性回復モデルマージの設計空間と評価の落とし穴.md`）に向け、以下 2 件の正式分析成果物および再現可能な CPU 専用集計スクリプトを整備する。

1. **P4 因果切り分け（`safety+code, α=0.6, seed42`）の Before/After 正式比較表**
   - `v5/results/rope_theta_ablation/` に完了した `rope_theta=1,000,000` 再評価結果と、`v3/results/vllm/debug_limit320/merged/seed42/safety+code/` の元結果（`rope_theta=10,000`）を対比する。
   - HarmBench / WildGuard / StrongREJECT の 3 分類器個別 ASR、従来ルール VRR、Valid 中の文字化け率、拡張 VRR、HumanEval / MBPP / Code Avg を 1 表にまとめ、草稿 5.3 節の因果結論を定量確定する。
2. **WizardMath 公式 Alpaca-CoT GSM8K（55% スケール）× 安全性 最終集計・曲線プロット・ブートストラップ解析**
   - `v5/results/math_alpaca_cot/` 配下の完了済み JSON を自動走査し、既存の安全性結果（`v5/results/fp32_sst_math/`・`v3/results/vllm/debug_limit320/`）と結合する。
   - 現時点（`117/138`）で即座に中間集計・図表を生成でき、`seed 44` 完了後（17:00 ごろ）に再実行するだけで `138/138` 全 3 seed 最終版へそのまま更新できる設計とする。

## 2. 設計方針と変更対象
- **非改変制約 (NFR2)**: `v3/`・`v1/`・`v2/` は一切変更せず読み取り専用とする。すべてのスクリプト・テスト・出力は `v5/` 配下に作成する。
- **CPU 専用実行**: `h200-01` の GPU0 障害を回避するため、全スクリプトで `CUDA_VISIBLE_DEVICES=""` を強制する。
- **変更・作成ファイル**:
  - `v5/scripts/summarize_rope_theta_ablation.py`: Before/After 比較表（Markdown + JSON）生成スクリプト。結論箇条書きの数値も集計辞書から動的に埋め込み、表と本文の不一致を防ぐ。
  - `v5/scripts/analyze_math_alpaca_cot.py`: 全 11 手法 × 全 α × 完了 seed の集計、妥当性制約付き（拡張 VRR ≥ 80%）Pareto フロンティア抽出、プロンプト単位ペアードブートストラップ（1,000 回、固定 seed `20261124`）、および論文用図 3 枚の描画スクリプト。
  - `v5/tests/test_math_alpaca_cot.py`: モデル名パーサ・Pareto 抽出・Code pass@1 抽出の単体テスト追加。

## 3. 検証計画
1. `py_compile` で両スクリプトの構文チェックを行う。
2. CPU 環境で両スクリプトを実行し、Markdown / JSON / PNG 出力を生成する。
3. 生成した Markdown の全数値と、PNG 画像 3 枚の視覚レイアウト（凡例・ラベル重なり・軸範囲）を目視確認する。
4. `pytest v5/tests -q` で全単体テストの PASS を確認し、`git status --short -- v3/scripts v3/results v1 v2` で NFR2 遵守を確認する。
