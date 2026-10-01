# 実装計画: results/summary_tables への 3-seed 標準偏差 (std) 算出・表示対応

`v3/results/summary_tables/` 内に出力されるすべての評価結果表（Markdown および CSV）において、従来の 3-seed 平均値 (`Mean%`) 表記から、3-seed の平均値と標準偏差を併記する `Mean ± Std%` 表記へ更新・再集計を行います。

## ユーザー確認事項 (User Review Required)

> [!IMPORTANT]
> - 標準偏差 (std) は **3つの seed (42, 43, 44)** 間で計算されます（不偏標準偏差 `ddof=1` を使用、データ数1の場合は `0.00`）。
> - ドメイン平均（例: `Math Ave`）については、各 seed におけるドメイン平均値を算出した上で、3-seed 間の Mean と Std を計算します。
> - 出力形式は Markdown 表および CSV 表ともに `XX.XX ± YY.YY%`（または PPL 等単位がないものは `XX.XX ± YY.YY`）と表記します。

## 変更対象コンポーネント

---

### 集計スクリプト (Analysis Scripts)

#### [MODIFY] [generate_summary_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_summary_tables.py)
- 各 seed (42, 43, 44) 毎の各指標およびドメイン平均スコアを集計した上で、3-seed 間の Mean および Std を計算するロジックを実装。
- `format_markdown_table` および CSV 出力部分で `f"{mean:.2f} ± {std:.2f}%"` フォーマットに整形。

#### [MODIFY] [generate_paper_summary_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_paper_summary_tables.py)
- 論文用サマリーテーブル (`paper_evaluation_summary_tables.md` / `paper_summary_*.csv`) の集計処理を 3-seed Mean ± Std 対応に変更。

#### [MODIFY] [generate_ablation_additive_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_ablation_additive_tables.py)
- アブレーション評価比較表 (`ablation_additive_summary_tables.md` / `.csv`) を Mean ± Std 対応に変更。

#### [MODIFY] [generate_valid_asr_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_valid_asr_tables.py)
- 有効応答 ASR 比較表 (`valid_asr_summary_tables.md` / `.csv`) を Mean ± Std 対応に変更。

#### [MODIFY] [aggregate_base_vs_main.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/aggregate_base_vs_main.py)
- `paper_evaluation_summary_tables.md` の文字列パース（`±` 対応）および `base_vs_main_summary.md` への Mean ± Std の反映。

---

## 修正手順と再生成コマンド

1. 上記 5 つの Python スクリプトを修正。
2. ターミナルでスクリプトを実行し、`v3/results/summary_tables/` 内の全ファイルを更新。
   - `python v3/scripts/analysis/generate_summary_tables.py`
   - `python v3/scripts/analysis/generate_paper_summary_tables.py`
   - `python v3/scripts/analysis/generate_ablation_additive_tables.py`
   - `python v3/scripts/analysis/generate_valid_asr_tables.py`
   - `python v3/scripts/analysis/aggregate_base_vs_main.py`

## 検証計画 (Verification Plan)

### 手動検証
- ターミナルでの各スクリプト実行がエラーなく正常完了することを確認。
- 生成された `v3/results/summary_tables/evaluation_summary_tables.md` や `paper_evaluation_summary_tables.md` 等の主要ファイルをビューアで開き、スコアが `XX.XX ± YY.YY%` 形式で正しく出力されていることおよび数値計算が正しいことを確認。
