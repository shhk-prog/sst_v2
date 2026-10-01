# Ablation Additive (Addactive) 結果集計の実施計画

アブレーション実験における `additive` (ユーザー表記 `addactive`) 変分などの評価結果 JSON から各評価指標（Safety / Math / Code / Medical / General）を自動抽出し、比較・集計テーブルを生成します。

## ユーザー確認事項

> [!NOTE]
> 「addactive」はアブレーション設定におけるマージ変分（variant）の **`additive`** を指していると解釈して集計を行います。`interpolation` との比較表および `additive` 条件下の詳細スコア表を作成します。

## 概要・目的

1. `v3/results/debug_limit320/merged` （および関連ディレクトリ）内の JSON ファイルから、アブレーション実験データ（特に `variant=additive`）を検索・集計する。
2. 集計スクリプト `v3/scripts/analysis/generate_ablation_additive_tables.py` を作成し、手法（diagonal_sst / data_free_sst）、α パラメータ、シード平均（42, 43, 44）ごとにテーブル化する。
3. `v3/results/summary_tables/ablation_additive_summary_tables.md` および `.csv` へ結果を出力する。

## 変更・追加ファイル一覧

### [Component: Analysis Scripts]

#### [NEW] [generate_ablation_additive_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_ablation_additive_tables.py)
- アブレーション実験用結果抽出・集計スクリプト。
- `variant`（`additive` vs `interpolation`）、`sst_ratio`（`Fh/Fb` 等）、サンプルサイズ等の条件軸でフィルタリング・グループ化し、5大ドメイン平均および各ベンチマークのスコアを表形式で出力。

### [Component: Results & Documentation]

#### [NEW] [ablation_additive_summary_tables.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/results/summary_tables/ablation_additive_summary_tables.md)
- 生成される集計結果マークダウンレポート。

#### [NEW] [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/ablation_additive_summary/task.md)
- タスク管理用リスト。

#### [NEW] [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/ablation_additive_summary/implementation_plan.md)
- 実装計画書。

#### [NEW] [walkthrough.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/ablation_additive_summary/walkthrough.md)
- 作業完了後の修正・集計内容の確認ドキュメント。

## 検証計画

### 自動化スクリプト実行
- `python3 v3/scripts/analysis/generate_ablation_additive_tables.py` を実行（Pythonスクリプトによる内部検証およびテーブル生成確認）。
- 出力された `.md` および `.csv` ファイルが存在し、非空かつ期待通りの行・列が含まれていることを確認。
