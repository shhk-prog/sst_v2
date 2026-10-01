# FLMSEC LaTeX表修正 Walkthrough

## 実施日時
2026-08-17

## 実施内容

### 1. vllm環境の削除
- condaコマンドがサンドボックスで利用不可のため、通常のターミナルで手動実行が必要
- コマンド: `conda env remove -n vllm -y`

### 2. `generate_flmsec_hyo.py` の修正
| 修正箇所 | 変更内容 |
|---|---|
| `format_latex_table()` | `tabularx` + `R` 列指定子 → `\resizebox{\textwidth}{!}{\begin{tabular}...\end{tabular}}` |
| キャプション | `_` `%` をエスケープ (`safe_title`) |
| 列指定子 | `R` → `r` |
| `main()` 関数 | vllmディレクトリの読み込みを削除。`normal` のみに統一 |

### 3. `replace_case_study.py` の修正
- `\end{tabularx}` → `\end{tabular}` + `}` に修正（auc_table, new_table両方）

### 4. `replace_cost_tables.py` の修正
- `table_cost`, `table_gpu` の `\end{tabularx}` → `\end{tabular}` + `}` に修正
- old_*マッチング用のパターンも `\end{tabular}` + `}` に修正

### 5. `generate_gpu_table.py` の修正
- `\end{tabularx}` → `\end{tabular}` + `}` に修正
- 列指定子 `X` → `l` に変更
- 正規表現パターン `[t]` → `[tH]` に変更（`[H]`オプションにも対応）

### 6. `flmsec.md` の本文表修正
以下の表を `\resizebox{\textwidth}{!}{\begin{tabular}...\end{tabular}}` に変換:
- `tab:simple_prelim` (行636): `tabularx{llcRRR}` → `tabular{llcrrr}`
- `tab:evaluation_main_alpha=0.6` (行697): `tabularx{llcRRRRR}` → `tabular{llcrrrrr}`
- `tab:evaluation_yobi_main_GSM8K` (行754): `tabularx{llRRRR}` → `tabular{llrrrr}`
- `tab:yugaioutou_rei` (行845): `tabularx{lp{6cm}}` → `tabular{lp{10cm}}`
- `tab:cost` (行875): `tabularx{lcccc}` → `tabular{lcccc}`
- `tab:gpu` (行949): `tabularx{p{6cm}rr}` → `tabular{lrr}`

※ `tab:evaluation_metrics` (行528) は `X` 列（折り返し必要）のため `tabularx` のまま維持

### 7. `flmsec.md` の自動生成LaTeX表セクション置換
- 行1149〜3914: `generate_flmsec_hyo.py` が生成した新しいLaTeX表（`\resizebox` + `tabular`）に置換
- 旧vllmデータのappendixセクションを全削除

## 検証結果

| 項目 | 結果 |
|---|---|
| `\end{tabularx}` 残存数 | 0 件 ✅ |
| `\begin{tabularx}` 残存 | 1件（`tab:evaluation_metrics`、X列使用で意図的） ✅ |
| `\resizebox` 適用数 | 121箇所 ✅ |
| `vllm` データ | 0件 ✅ |
| 全スクリプト実行 | 全て正常完了 ✅ |

## スクリプト実行順序（今後）
```bash
source venv_v3/bin/activate
python3 scripts/analysis/generate_flmsec_hyo.py 
python3 scripts/analysis/generate_three_panel_plot.py 
python3 scripts/analysis/generate_case_study.py
python3 scripts/analysis/replace_case_study.py
python3 scripts/analysis/replace_cost_tables.py
python  scripts/analysis/generate_gpu_table.py
```
