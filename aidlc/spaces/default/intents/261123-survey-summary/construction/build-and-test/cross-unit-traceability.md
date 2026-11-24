# 要件の網羅確認（Unit なし）

判定: **pass**。未対応の ID は 0 件。出力元: `aidlc engine sensor-traceability --stage build-and-test`。

Unit の分割は無い（zero-Unit）。所有する段階は、すべて `code-generation`。

| ID | 対応 | 実装・検証のファイル |
|---|---|---|
| FR1.1 | 対応 | `v5/docs/survey_summary/preregistration.md` |
| FR1.2 | 対応 | `v5/src/v5lib/compare.py` |
| FR1.3 | 対応 | `v5/src/v5lib/metrics.py` |
| FR1.4 | 対応 | `v5/src/v5lib/metrics.py` |
| FR1.5 | 対応 | `v5/src/v5lib/compare.py` |
| FR2.1 | 対応 | `v5/docs/survey_summary/preregistration.json` |
| FR2.2 | 対応 | `v5/scripts/run_pipeline.py` |
| FR2.3 | 対応 | `v5/src/v5lib/hypotheses.py` |
| FR2.4 | 対応 | `v5/scripts/run_pipeline.py` |
| FR2.5 | N/A | V12〜V16 は実装しない（必須ではない。考察の補足の範囲） |
| FR3.1 | 対応 | `v5/scripts/regen_flmsec_tables.py` |
| FR3.2 | 対応 | `v5/scripts/plot_pareto_curves.py` |
| FR3.3 | 対応 | `v5/scripts/ablation_table.py` |
| FR3.4 | 対応 | `v5/src/v5lib/manifest.py` |
| FR3.5 | 対応 | `v5/README.md` |
| FR4.1〜FR4.3 | 対応 | `v5/docs/survey_summary/report.md` |
| FR5.1〜FR5.3 | 対応 | `v5/docs/survey_summary/report.md` |
| FR6.1 | 対応 | `v5/scripts/build_report.py` |
| FR6.2 | 対応 | `v5/src/v5lib/report.py` |
| NFR1 | 対応 | `v5/tests/test_outputs.py` |
| NFR2 | 対応 | `v5/src/v5lib/safeio.py` |
| NFR3 | 対応 | `v5/src/v5lib/report.py` |
| NFR4 | 対応 | `v5/src/v5lib/tensor_checks.py` |
| NFR5 | 対応 | `v5/README.md` |

ブラウザで動く機能は無い。
