<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-23T15:01:09Z — ベンチマーク ASR は、論文の B_i（二値）に合わせ、results[] の `asr > 0.5` の件数 / 全件とした。旧表の「Bench. ASR」列が何から作られたかは未確認で、論文の表との照合（Part B）で食い違えば、不一致の一覧に出る
- 2026-11-23T15:01:09Z — 仮説 V1〜V11 の判定の指標、支持と反証の閾値、採用基準の細目、正規化の方法は、依頼者の決定に無いため実装担当が提案値として preregistration.json/.md に固定した。Part B の前に依頼者の確認が必要
- 2026-11-23T15:01:09Z — V5 の「注入量」は ⟨θ_merged − θ_u, δ_s⟩ の SST/TA 比の中央値、4 ドメインの θ_u は sst.py の param_util_mean（3 モデルの平均）に合わせた。V4 の ulp は fp16 の正規数 2^(floor(log2|x|)-10)、非正規数は 2^-24 とした
- 2026-11-23T15:01:09Z — 実測しなくても分かる性質: sst.py と同じ fp16 演算では、F̄_b=0 のとき分母が約 9.5e-7 になり、F_h が約 0.0625 を超えると λ が inf（65504 超）になる。V2 の inf の数は、実データで多くなる可能性がある（合成テストで確認。実データは未確認）
- 2026-11-23T15:01:09Z — results_io の走査（ファイル名の解析だけ。JSON の中身は開いていない）を v3/results/vllm/debug_limit320 に対して 1 回実行し、9,965 件すべてを解析できた（解析不能 0、欠損 0、新旧併存のタスク 173 件）。ファイル名の規則の検証が目的で、読み取りだけ

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-23T15:01:09Z — `v5/pytest.ini` を 1 つ追加（`-p no:hydra_pytest`）。venv_sst の hydra pytest プラグインが antlr のバージョン不一致で壊れており、`python -m pytest` が起動できないため。unit-test-instructions.md の「設定ファイルは置かない」から外れる。venv は変更していない
- 2026-11-23T15:01:09Z — 単体テストは 49 件（計画の目安は約 20 件）。各ファイルに異常系・境界を足したため
- 2026-11-23T15:01:09Z — 計画に無いモジュールを追加: manifest.py（Step 6.4）、verify.py（V1〜V11 の実行部分。スクリプトを薄くするため）、tensor_checks.py（テンソル計算）、report.py（Step 10.1 の本体）、scripts/_common.py、tests/synth.py（合成データを作る関数）
- 2026-11-23T15:01:09Z — 書き込み許可ルートを替える環境変数 V5_WRITE_ROOT_FOR_TESTS を safeio.py に追加（テスト専用。tmp_path への書き込みのため）。本番では設定しない
- 2026-11-23T15:01:09Z — check_v1_v9.py は、計画の Step 7.3 の機能に加え、--approved-by-user が無いと実行しない（--dry-run は可）。FR2.4 をスクリプト側でも確認するため。check_inputs.py と check_v10_v11.py は、実データのテンソルを開かないので許可の引数を要求しない（run_pipeline.py の --execute は要求する）
- 2026-11-23T15:01:09Z — ステップ 11.2: traceability.json の FR4.1〜4.3、FR5.1〜5.3 は計画どおり GAP（Part B 後に OK）。FR2.5 は N/A（理由つき）。センサーの失敗は、この 6 件の GAP だけ

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-23T15:01:09Z — 範囲を絞った実行は、途中で「支持」に当たる値が出ても必ず「判定不能」にした（計画の方針）。代わりに、実行範囲と部分的な値は出力に記録される。範囲を絞った探索の結果から機構を主張することは避けられるが、全範囲の実行（FIM は数十 GB）が必要になる
- 2026-11-23T15:01:09Z — 論文の表との照合は、LaTeX を読む簡易パーサ（multirow と `$m \pm s$` の形だけ）にした。表の形が違う箇所は「論文の値を読めない」に出る。汎用の LaTeX パーサは作らなかった
- 2026-11-23T15:01:09Z — 曲線は、除外した点（VRR が下限未満）も α の順の線でつなぎ、記号 × で区別した。補間はしない

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-23T15:01:09Z — 仮説の閾値（V1〜V11）と採用基準の細目は、依頼者の確認を受けてよいか（提案値のまま Part B に進むか）
- 2026-11-23T15:01:09Z — check_v1_v9 の dry-run の入力確認で、model_weights_util が「なし」だった（HF のキャッシュに 3 つのドメインモデルのスナップショットが揃っていない）。base は見つかった。ドメインモデルのフォルダを --wizardmath-dir、--wizardcoder-dir、--medalpaca-dir で指定する必要があるか、V4、V5、V6 は判定不能のままか
- 2026-11-23T15:01:09Z — 論文の主結果の表（appendix.tex）が、旧表のどの列・どの有害判定から作られたかは未確認。照合（Part B）の結果で、判定差と不一致の割合を見て判断する
- 2026-11-23T15:01:09Z — アブレーションの k の格子（0.05、0.1、0.2、0.5）のうち、v3 の結果にあるのは k=0.2 のみ（safety+math の sst で確認）。表の大半は N/A になる見込み。V10 の判定にも影響する
