# 修正内容の確認 (Walkthrough): results/summary_tables への 3-seed 標準偏差 (std) 算出・表示対応および Table 4 / 5 自動生成機能

`v3/results/summary_tables/` 内に出力されるすべての評価結果表（Markdown および CSV）において、3-seed (seed 42, 43, 44) の平均値と標準偏差（`Mean ± Std%`）を正確に計算し表示するように集計スクリプト群を改修いたしました。

さらに、論文『secure-merge_統一比較評価論文_改訂版.md』で引用される **Table 4** および **Table 5** を動的に 3-seed Mean ± Std で自動集計・出力する専用スクリプト `generate_paper_tables_4_and_5.py` を作成いたしました。

---

## 新規作成・改修スクリプト一覧

### 1. **[`generate_paper_tables_4_and_5.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_paper_tables_4_and_5.py)** 【新規・不具合修正済み】
- **Table 4**: 主要マージ手法（$\alpha=0.6$, $k=0.20$ または単一/既定実行）における詳細評価指標（Harmful ASR, Valid response rate, Valid Safety Rate, GSM8K, HumanEval 等）の 3 Seeds Average (Mean ± Std) 比較表の自動集計。
- **Table 5**: `safety+math` における `diagonal_sst_main` の $\alpha \in [0.2, 0.6, 0.8, 1.0]$ スイープにおける Refusal ASR, Harmful Content ASR, GSM8K, 定量的評価注記の自動集計。
- `--update_paper` オプションで論文ドラフトへ自動直接置換・反映可能。
- **不具合修正**: `--update_paper` 実行時に発覚した `NameError: name 're' is not defined` を解決するため、スクリプト先頭に `import re` を追加・修正しました。

### 1-b. **[`generate_preliminary_table.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_preliminary_table.py)** 【新規】
- **Table 3b (予備実験)**: `v3/results` 配下からファイル名に `trustllm` または `beavertails` を含む JSON 結果を動的に走査し、TrustLLM (ASR) と BeaverTails (Utility) の 3-seed Mean ± Std の評価表を自動生成します。
- `--update_paper` オプションで論文ドラフト (Section 6) へ Table 3b として自動追記/置換します。

### 2. **既存スクリプトの改修**
- **[`generate_summary_tables.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_summary_tables.py)**: 3-seed 不偏標準偏差（`ddof=1`）集計に対応。
- **[`generate_paper_summary_tables.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_paper_summary_tables.py)**: 論文用 5 大ドメイン平均の Mean ± Std 化。
- **[`generate_ablation_additive_tables.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_ablation_additive_tables.py)**: アブレーション表の Mean ± Std 化 & CLI 引数対応。
- **[`generate_valid_asr_tables.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_valid_asr_tables.py)**: 有効応答 ASR の Mean ± Std 化 & `NoneType` ガード。
- **[`update_appendix.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/update_appendix.py)**: Appendix 38 カラム比較表の自動置換・同期機能。

---

## 3. **論文ドラフトの最新状態**
- `docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md`
  - セクション 5.4: 予備実験（TrustLLM/BeaverTails等による小規模基礎検証と単一評価器の限界・偽の安全性）と本実験（最新4安全ベンチマーク、多ドメイン、3-seed統計処理、推論崩壊の分析）の実験設定の詳細な差分を整理・明記。
  - セクション 6.1: `mean ± std`（不偏標準偏差 `ddof=1`）による統計的表記の記述を反映。
  - Table 4 & Table 5: スクリプトによる動的集計・論文置換に対応。

---

## ターミナル実行コマンド一覧

```bash
# 1. 全基本サマリーテーブルの生成
python3 scripts/analysis/generate_summary_tables.py --results_dir results/debug_limit320/merged --output_dir results/summary_tables --target_alpha 0.6
python3 scripts/analysis/generate_paper_summary_tables.py --results_dir results/debug_limit320/merged --output_dir results/summary_tables --target_alpha 0.6
python3 scripts/analysis/generate_ablation_additive_tables.py --results_dir results/debug_limit320/merged --output_dir results/summary_tables --target_alpha 0.6
python3 scripts/analysis/generate_valid_asr_tables.py --results_dir results/debug_limit320/merged --output_dir results/summary_tables --target_alpha 0.6

# 2. Table 4 及び Table 5 の集計・出力（--update_paper を付与すると論文へ直接自動反映）
python3 scripts/analysis/generate_paper_tables_4_and_5.py --results_dir results/debug_limit320/merged --output_dir results/summary_tables --target_alpha 0.6 --update_paper

# 3. Appendix の自動同期
python3 scripts/analysis/update_appendix.py
```
