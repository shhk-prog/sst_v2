# SST-Merge 評価結果の集計・可視化ワークフロー

このドキュメントは、SST-Merge実験の評価結果を集計し、グラフや表を生成するための正しいワークフローを説明します。

## ✅ 正しいワークフロー

### 1. 結果の集計
```bash
python3 scripts/analysis/collect_all_results.py
```

**出力**: `all_eval_results_summary.json`（プロジェクトルートに生成）

このスクリプトは以下のディレクトリから結果を収集します：
- `eval/finetuned/` - ベースモデル
- `eval/merged/baseline/` - Task Arithmetic、DARE、TIES
- `eval/merged/sst_merge/` - SST-Merge（Additive/Interpolation）
- `eval/merged/data_free/` - Data-Free SST-Merge
- `eval/merged/interpolation/` - Interpolation（GEVP ON/OFF）

### 2. グラフの生成
```bash
python3 scripts/visualization/visualize_sst_merge_detailed.py
```

**入力**: `all_eval_results_summary.json`
**出力**: `docs/evaluation_results_202602/*.png`（26個の詳細グラフ）

生成されるグラフ：
- ベースライン手法（2グラフ: A5_A7、A6_A7）
- SST-Merge Additive（6グラフ: k=5,10,20 × 2ペア）
- SST-Merge Interpolation（6グラフ: k=5,10,20 × 2ペア）
- Data-Free Additive（6グラフ: k=5,10,20 × 2ペア）
- Data-Free Interpolation（6グラフ: k=5,10,20 × 2ペア）

### 3. 表の生成

#### ⚠️ 重要な注意点

**`>>`（追記）を使用する場合、既存のファイルに内容が追加されます！**

既存の`tables.md`がある場合、以下の選択肢があります：

#### オプションA: 新規作成（推奨）
```bash
# 既存ファイルを削除または移動
rm docs/SST_Merge_Tables_Analysis/tables.md
# または
mv docs/SST_Merge_Tables_Analysis/tables.md docs/SST_Merge_Tables_Analysis/tables_old.md

# Data-Dependent表を生成（新規作成）
python3 scripts/analysis/generate_data_dependent_tables.py > docs/SST_Merge_Tables_Analysis/tables.md

# Data-Free表を追記
python3 scripts/analysis/generate_data_free_tables.py >> docs/SST_Merge_Tables_Analysis/tables.md
```

#### オプションB: 追記（既存内容を保持）
```bash
# Data-Dependent表を追記
python3 scripts/analysis/generate_data_dependent_tables.py >> docs/SST_Merge_Tables_Analysis/tables.md

# Data-Free表を追記
python3 scripts/analysis/generate_data_free_tables.py >> docs/SST_Merge_Tables_Analysis/tables.md
```

**注意**: オプションBを使用すると、実行するたびに同じ表が重複して追加されます！

## 📋 各スクリプトの入力ファイル

| スクリプト | 入力 | データソース |
|-----------|------|------------|
| `visualize_sst_merge_detailed.py` | `all_eval_results_summary.json` | 集計済みデータ |
| `generate_data_dependent_tables.py` | 直接JSONファイル（`eval/merged/`以下） | 生データ（`rglob`で検索） |
| `generate_data_free_tables.py` | `all_eval_results_summary.json` | 集計済みデータ |

## 🔍 データソースの違い

- **`generate_data_dependent_tables.py`**: 
  - `eval/merged/`ディレクトリ内のJSONファイルを**直接**読み込む
  - `all_eval_results_summary.json`を使用**しない**
  
- **`generate_data_free_tables.py`**: 
  - `all_eval_results_summary.json`を使用
  - `collect_all_results.py`の実行が必要

## 💡 推奨ワークフロー

```bash
# Step 1: 結果を集計
python3 scripts/analysis/collect_all_results.py

# Step 2: グラフを生成
python3 scripts/visualization/visualize_sst_merge_detailed.py

# Step 3: 既存の表ファイルをバックアップ（オプション）
mv docs/SST_Merge_Tables_Analysis/tables.md docs/SST_Merge_Tables_Analysis/tables_backup_$(date +%Y%m%d).md

# Step 4: 表を生成（新規作成）
python3 scripts/analysis/generate_data_dependent_tables.py > docs/SST_Merge_Tables_Analysis/tables.md
python3 scripts/analysis/generate_data_free_tables.py >> docs/SST_Merge_Tables_Analysis/tables.md

echo "✅ 完了！"
```

## 🎯 まとめ

ユーザーが提案したワークフローは**ほぼ正しい**ですが、以下の点に注意が必要：

1. ✅ `collect_all_results.py` → `all_eval_results_summary.json`の生成は正しい
2. ✅ `visualize_sst_merge_detailed.py`でグラフ生成は正しい
3. ⚠️ `>> tables.md`を使う場合、既存内容に追記されるため、重複を避けるには最初の呼び出しで`>`（上書き）を使用すること
4. ℹ️ `generate_data_dependent_tables.py`は`all_eval_results_summary.json`を使わないため、`collect_all_results.py`の実行は不要（ただし、実行しても問題なし）
