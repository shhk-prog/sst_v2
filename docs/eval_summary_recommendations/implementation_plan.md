# 再実行計画: 評価タスクの再実行および集計反映

## 1. 目的
修正・改善を行った評価タスクのうち、再実行が必要なタスクのみを効率的に再測定し、全ベンチマークの完全な精度データを揃える。

## 2. タスク別再実行要否一覧

| タスク名 | 再実行要否 | 理由・状態 |
| :--- | :--- | :--- |
| **`general_ifeval`** | **要再実行** | Chat Template 未適用時代の生成結果を修正版 `eval_utility.py`（Chat Template 適用＋繰返し裁断）で生成し直すため |
| **`general_mmlu_pro`** | **要再実行** | 以前の抽出エラー版 JSON は削除済みであり、修正後の `extract_mmlu_pro_answer` で正しく計測し直すため |
| **`general_mmlu`** | **不要** | 最初から 4 択対数尤度比較で正しく正常評価済み |
| **`math_gsm8k`** | **不要** | `flexible-extract` により最初から正常評価済み |
| **`math_minerva_math500`** | **不要** | `math-verify` (数式構造判定) により最初から正常評価済み |
| **`medical_medqa_4options`** | **不要** | 4 択対数尤度比較で最初から正常評価済み |
| **`medical_pubmedqa`** | **不要** | 3 択対数尤度比較で最初から正常評価済み |
| **`inst_evol_code`** | **不要** | PPL & Sim Score 複合指標で最初から正常評価済み |
| **`inst_medalpaca`** | **不要** | PPL & Sim Score 複合指標で最初から正常評価済み |
| **`alpaca_eval2`** | **不要** | 生成・評価は完了済み。集計 `pareto_auc.py` の修正のみで LC Win Rate が即時反映されるため |

## 3. 推奨再実行手順
以下のコマンドを実行することで、`general_ifeval` と `general_mmlu_pro` のみが正しく再評価されます。
```bash
python3 scripts/run_base_eval_parallel.py --config configs/config_main.yaml
```
