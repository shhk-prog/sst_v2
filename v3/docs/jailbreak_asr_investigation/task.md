# タスク: General/Inst Ave (%) 算出計算式の正常化・歪み解消

## 目的
`General/Inst Ave (%)` の算出において、文字完全一致度 (`Evol-Code Similarity`, `MedAlpaca Similarity`) などの尺度の異なる極低ノイズ指標を除外し、標準的・学術的な一般知識・指示追従ベンチマーク（**MMLU**, **IFEval**, **AlpacaEval 2**）の 3 タスク平均として再定義・正常化する。

## タスクリスト
- [ ] `generate_summary_tables.py` 内の `row_to_dict` における `General/Inst Ave (%)` の計算対象を `["mmlu", "ifeval", "alpaca_eval2"]` の 3 タスクに正常化
- [ ] `generate_paper_summary_tables.py` 内の `row_to_dict` における `General/Inst Ave (%)` の計算対象を `["mmlu", "ifeval", "alpaca_eval2"]` の 3 タスクに正常化
- [ ] ドキュメント (`implementation_plan.md`, `walkthrough.md`) の更新
