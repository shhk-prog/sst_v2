## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-23T16:09:41Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | v5/docs/survey_summary/report.md > 3.0 節「観測事実」と 3.4 節の表（評価（判定器）の違い: 「観測事実（強い）」） | 「論文の表の Conditional ASR はベンチマーク別の分類器で作られている」を「強い」観測事実としているが、根拠は `native_classifier_probe.md` の一部の例だけである。一致例（DARE、DELLA、Task Arithmetic と TIES と Matena-Fisher の safety+medical）だけを引き、同じプローブ内の不一致（Matena-Fisher safety+code は 63.24 で論文 65.04、Task Arithmetic safety+code は 59.29 で論文 60.91、SafeMERGE safety+code は 0.31 で論文 0.34）には触れていない（LED-Merging の 70.89 対 71.01 だけ書いている）。ベンチマーク別の分類器で作った値は `paper_comparison.md` の照合に入っておらず、一致件数がない。単体モデルの行（論文の MedAlpaca 62.85、WizardCoder 73.99、WizardMath 67.62）はプローブの対象外である。プローブ自身も「探索用、集計の細部は未確認」と書いている。safety+medical の 2 つの手法は seed が 2 本だけである。`paper_comparison.md` の「判定差」が 0 件なのも、この判定器を比べていないからで、FR3.1 の「判定差を別項目にする」を満たしたことにならない。 | ベンチマーク別の分類器の値を、他の列と同じ許容差（0.005）で論文の表 216 件すべてと照合し、一致、不一致、単体モデルを含めた件数を出す。それまで 3.4 節の「強い」を「示唆（一部の手法で再現、残りは未確認）」に下げ、不一致の例（Matena-Fisher、Task Arithmetic、SafeMERGE）も 3.0 節に書く。 | New |
| R-02 | Major | v5/docs/survey_summary/report.md > 3 節全体。`traceability.json` の FR4.3（target は report.md） | FR4.3 は、SAGAI_EN_sst の定式化と v3 の実装の違い（`architecture.md` の対応表）を踏まえた理論面の考察を求める。しかし report.md には、論文の式と実装を対比した記述も、`architecture.md` の対応表への参照もない。論文と実装の違いは、擬似コードの 1 行（「additive。interpolation は比較として残す」）と、4.3 の評価点の注記だけである。3.1 節の SST が TA より注入量が少ないという説明は `code-quality-assessment.md` に頼っている。それなのに traceability は FR4.3 を OK としている。 | FR4.3 に当たる小節を 3 節に足し、論文の式と v3 の実装（interpolation と additive、FIM の評価点、fp16 の扱い）の違いを、`architecture.md` の対応表を出典にして書く。足さない場合は、FR4.3 を OK でなく部分対応として traceability に書き直す。 | New |
| R-03 | Minor | v5/docs/survey_summary/report.md > 2.4 節の V11 の行（自動生成）と 3.1 節 | 自動生成の 2.4 節は、V11 を「支持」としか出さない。実際は safety+code で TA だけが SST を支配し、safety+math と safety+medical では双方が支配し合っている。事前登録の指標（1 組でも支配すれば数える）が緩く、「SST が一貫して優れる」は意味しない。この注意は手書きの 3.1 節にしかなく、2.4 節だけを読む人は誤読する。ただし、規則どおりの判定そのものは正しい。 | `build_report.py` が V11 の行に、`ta_dominates_sst` の枠の数と、双方が支配し合う枠があることを自動で添える。 | New |
| R-04 | Minor | v5/docs/survey_summary/report.md > 2.4 節の V7、V8、V9 の行と 3.2 節 | V7、V8、V9 の行にも、全体の実行範囲（safety+math、seed 42）がそのまま付く。だが、この 3 つは `complete: true` で範囲を絞っておらず、V7 は safety+code のモデルを見ている。範囲の表示と判定が矛盾して見える。V8 を「不支持」とし 3.2 節で「原因ではないと言える」と断定する根拠は、各ファイルの先頭 20 件がプレースホルダでないこと（`placeholder_fraction=0`）だけで、実際に FIM の推定に使ったキャッシュは見ていない。 | 仮説ごとに、その仮説が実際に見た範囲を表示する。3.2 節の V8 の文は、「先頭 20 件のデータファイルで、プレースホルダは見つからなかった」のように、見た範囲に合わせて弱める。 | New |
| R-05 | Minor | `traceability.json` の FR1.1（target は preregistration.md）、および `v5/scripts/probe_native_classifier.py` | FR1.1 は「レポートの冒頭に書く」要件だが、target は preregistration.md になっている。実体は report.md の 1 節である。`probe_native_classifier.py` は、3.0 節の中心的な主張の根拠なのに、`run_pipeline.py` の段階にも入っておらず、`--approved-by-user` の仕組みも、テストもない（`verify.py` と `tensor_checks.py` は `open_readonly` を通さずに `open(..., "r")` している箇所もあるが、読み取り専用であり実害はない）。 | FR1.1 の target を report.md に直す。プローブを pipeline の段階にして、合成データの小さなテストを足す。 | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `venv_sst/bin/python -m pytest v5/tests -q`（ワークスペース直下で実行） | 49 passed in 5.35s | 期待どおり。`assert True` のような常に通るテストは見つからなかった。ただし、プローブ、report.md の手書き部分の主張、V7〜V9 の実データ範囲は、テストの対象外である。 |
| 書き込み先の確認（`safeio.py`） | `resolve_write_path` が v5/ の外を `OutsideWriteRootError` にする。シンボリックリンクは解決してから判定する。入力は `open_readonly` が r と rb だけを許す | NFR2 を満たす。GPU は `CUDA_VISIBLE_DEVICES=""` と `device="cpu"` で固定され、NFR4 も満たす。 |
| 閾値の直書き | VRR の下限、許容範囲 2.0 pt、論文照合の許容差 0.005、V1〜V11 の基準は、すべて `preregistration.json` から読んでいる。コードに残る数値は、ベンチマーク分類器の定義（asr > 0.5、StrongREJECT の 0.5）と、格子（ALPHAS、K_GRID）である | 事前登録の整合は取れている。判定ロジック（`hypotheses.judge`）は、範囲を絞ると「判定不能」にし、基準の重なりを事前に拒否する。 |

### Summary

実装は、事前登録の読み込み、書き込みの制限、CPU 専用、判定規則の運用が堅く、テストも 49 件通っている。気になるのは、報告の主張の強さである。3.0 節の「論文の表はベンチマーク別の分類器で作られている」を、一部の一致例だけで「強い」観測事実とした点と、FR4.3（論文の式と実装の違いの考察）が実質的に書かれていない点を、承認前に比べてほしい。どちらも READY の範囲内（Major 2 件）で、レポートの文面と照合の追加で直せる。
