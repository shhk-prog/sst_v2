# ウォークスルー：SST-main = sst_merge_v5 再構成

実施日: 2026-05-01

## 実施内容

### Phase 1: 旧バージョンのアーカイブ

以下をすべて `archive/` に移動：
- `sst_merge_v2/`, `sst_merge_v3/`, `sst_merge_v3_src/`, `sst_merge_v4/`
- 旧実装: `src/`, `experiments/`, `analysis/`, `configs/`, `scripts/`
- 旧ログ: `logs/`（2025年12月分 88ファイル）→ `archive/logs_old/`
- `log_full_exp1/`

### Phase 2: docs/ 統合・カテゴリ再構成

`sst_merge_v5/docs/` + `/docs/` を統合し、カテゴリ別フォルダに整理：

| フォルダ | 内容 |
|---|---|
| `00_research_history/` | 研究進捗レポート8本（旧 guide/） |
| `01_quickstart/` | クイックスタート・評価データセット |
| `02_theory/` | 理論背景（GEVP、FIM） |
| `03_implementation/` | 実装ガイド群・スクリプトリファレンス |
| `04_experiments/` | 実験設計・実行ガイド |
| `05_results/` | 実験結果・分析・PNG図 |
| `06_robustness/` | ロバスト性・安全性検証 |
| `07_paper/` | 論文ドラフト（EN/JP）・付録 |
| `08_tables/` | LaTeX/MDテーブル |
| `09_rebuttal/` | リバッタル資料 |
| `10_lora_guides/` | LoRA関連 |

削除: `task.md`, `implementation_plan.md`, `walkthrough.md`（Antigravity管理ファイル）、論文コピー、`.bak`

### Phase 3: sst_merge_v5/ をルートへ昇格

`core/`, `scripts/`, `eval/`, `tests/`, `logs/`, `README.md` をルートへ移動。
`sst_merge_v5/` ディレクトリを削除。

## 最終構造

```
SST-main/（= sst_merge_v5）
├── core/          # sst_merge.py, data_free, interpolation
├── scripts/       # merging/, evaluation/, analysis/, visualization/, FT/
├── eval/          # finetuned/, merged/
├── tests/
├── logs/          # 現行ログ（4ファイル）
├── data/
├── docs/          # 148ファイル（11カテゴリ）
├── archive/       # 旧バージョン一式（366ファイル）
└── README.md      # v5版
```
