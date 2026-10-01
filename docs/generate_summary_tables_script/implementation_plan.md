# 集計テーブル生成スクリプト実装計画 (Summary Table Generation Plan)

## 概要
評価結果 JSON ディレクトリから、個別 Seed および Seed 平均の 4 つのドメインパターンに対して、指定された全 15 指標および 5 カテゴリ平均を含む集計テーブル（α=0.5固定比較表およびMerge手法別全α独立表）を出力する Python スクリプトを開発する。

## 実装仕様

### スクリプト作成位置
`file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_summary_tables.py`

### 主な機能
1. **JSONデータの自動パースと結果の読み込み**:
   - `results/debug_limit320/merged/seed{42,43,44}/{pattern}/{method}/` ディレクトリ構造に対応。
   - Safety (ASR↓), Math, Code, Medical, General/Instruction の各メトリクス値を浮動小数点 (%) に正規化。
2. **カテゴリ平均の自動計算**:
   - `Safety Ave`: (HarmBench + JailbreakBench + StrongReject + WildJailbreak) / 4
   - `Math Ave`: (GSM8K + Minerva Math500) / 2
   - `Code Ave`: (HumanEval + MBPP) / 2
   - `Medical Ave`: (PubMedQA + MedQA) / 2
   - `General/Inst Ave`: (MMLU + IFEval + AlpacaEval2 + Evol-Code + MedAlpaca) / 5
3. **Seed 平均処理**:
   - 各モデル設定 (pattern, method, alpha) に対する Seed 42, 43, 44 の平均値を算出。
4. **テーブル出力エンジン**:
   - **α=0.5 固定比較表**: `alpha=0.5` の全手法の成績を一覧比較。
   - **手法別独立表**: 各手法ごとに `alpha=0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0` などの全ハイパーパラメータを縦並び一覧化。
   - マークダウン (`.md`) または CSV (`.csv`) 形式でファイル書き出し可能。

## 動作確認
スクリプトのコードレビューおよび出力ファイルの生成ロジックの動作検証。
