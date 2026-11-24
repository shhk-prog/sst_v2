# コード生成計画：大規模調査のまとめ（v5）

## Summary

- Builds: v3/results/vllm の再集計（Validity-constrained Pareto 比較、FLMSEC 表の再現、k × variant 表、safety–utility 曲線）と、仮説 V1〜V11 の CPU 専用・読み取り専用の検証スクリプト、およびレポートの生成基盤
- Touches: 新設する `v5/`（`src/`、`scripts/`、`tests/`、`docs/survey_summary/`、`outputs/`、`README.md`）だけ。`v3/`、`v1/`、`v2/`、論文、既存結果は読むだけで変更しない
- Tests: pytest の単体テスト 約 20 件（要件ごとに 1 件以上、各コンポーネントに正常系 1 件）。合成の小さなデータで動かし、GPU と実データは使わない

## 前提と範囲

- 入力は `aidlc/spaces/default/intents/261123-survey-summary/inception/requirements-analysis/requirements.md`（以下 `requirements.md`）である。Unit の分割はない（zero-Unit）。`requirements.md` の ID（FR1〜FR6、NFR1〜NFR5）は、そのまま使う。
- 既存コードの調査は `aidlc/spaces/default/codekb/v3/`（`api-documentation.md` の「結果ファイル契約」、`code-quality-assessment.md` の「後続段階で要検証」V1〜V16）に従う。
- 作業場所は、ワークスペース直下の `v5/`（`v3/` と並ぶ新設フォルダ。現在は存在しない）。コマンドは、ワークスペース直下（`/mnt/nas/home/hiromi/src/sst_v2`）から実行する。
- Python は `venv_sst`（ワークスペース直下の環境）を使う。必要なパッケージ（numpy、matplotlib、torch、safetensors、pytest など）が無い場合は、勝手に入れず、依頼者に伝える。
- 実データを使う実行（Part B）は、この計画を作る範囲に含めるが、GPU は使わず、実行前に依頼者へコマンドを示して許可を得る（`requirements.md` の FR2.4、NFR4）。ビルドを担当する開発者（サブエージェント）は Part B を実行しない。
- ファイルの書き込み先は `v5/` に限る（NFR2）。`v3/results/vllm` などの入力は、読み取り専用で開く。

## Part A：コードとテストの生成（実データを使わない）

### Step 1：`v5/` の骨格と読み取り専用の入出力ガード

- [x] Step 1.1: `v5/README.md` を作る。何を行うフォルダか、実行場所、`venv_sst` の使い方、各スクリプトの役割、出力先、`v3/` を読み取り専用で扱うこと、GPU を使わないことを日本語で書く（FR3.5、FR6.1、NFR4、NFR5）
- [x] Step 1.2: `v5/src/v5lib/__init__.py` と `v5/src/v5lib/safeio.py` を作る。`safe_write(path)` は、書き込み先が `v5/` の下でなければ例外にする（NFR2）。`open_readonly(path)` は、`rb` または `r` だけで開く。出力先の既定は `v5/outputs/`
- [x] Step 1.3: `v5/scripts/` と `v5/tests/` と `v5/docs/survey_summary/` と `v5/outputs/` の置き場を作る（空の場所には `.gitkeep` を置かず、最初のファイルを書くときに作られるものとする）

### Step 2：テスト実行環境の確認（test-after の前提）

- [x] Step 2.1: `venv_sst/bin/python -m pytest --version` と、`import numpy, matplotlib` が通ることを確認する。`torch` と `safetensors` は、Step 7 の検証スクリプトが使うので、通るかを確認して `unit-test-instructions.md` に結果を残す。足りないパッケージは入れずに、依頼者へ報告する
- [x] Step 2.2: 単体テストの実行コマンドを `unit-test-instructions.md` に記録する（`venv_sst/bin/python -m pytest v5/tests -q`）

### Step 3：データ層（結果ファイルの読み込み。FR3.4、NFR2、NFR3）

- [x] Step 3.1: `v5/src/v5lib/results_io.py` を実装する。`v3/results/vllm/debug_limit320/merged/seed{42,43,44}/{pattern}/{method}/` の JSON のファイル名を解析する（`api-documentation.md` の「ファイル名の規則」）。解析する項目は、手法、パターン、α、seed、メトリクスの種類（安全性 4 種、有用性の新方式と旧方式）、アブレーションの条件（ratio、variant、k、層重み）。単発手法（α なし）は α を `None` にする。新方式と旧方式の有用性ファイルが併存するときは、glob の順序に依存せず、新方式を優先し、どちらを採ったかを記録する（`code-quality-assessment.md` F6）
- [x] Step 3.2: 同じ場所に `inventory(results_root)` を実装する。ファイル数、期待した条件に対する欠損、設定値の一覧を返し、入力ファイルのパスを必ず残す（FR3.4、NFR3）。`debug_limit320/base/` の単体モデルの結果も読む
- [x] Step 3.3: `v5/tests/test_results_io.py` を書いて実行する。合成の小さなディレクトリ（一時フォルダ）で、(a) 主実験と α なし手法のファイル名の解析、(b) 新旧併存時に新方式が採られて記録されること、(c) 欠損の条件が欠損の一覧に出ること、(d) `safe_write` が `v5/` の外への書き込みを拒否すること（NFR2）を確認する

### Step 4：指標層（FR1.3、FR1.4、FR3.1）

- [x] Step 4.1: `v5/src/v5lib/metrics.py` を実装する。安全性 JSON の `results[]` から、FLMSEC 論文（`neurips_2026.tex` L283-294）の定義で、VRR（妥当な応答の割合）、Conditional ASR（妥当な応答のうち有害と判定された割合）、VSR（妥当で有害でない応答の割合）、ベンチマーク ASR を計算する。妥当性は `is_gibberish` から取り、恒等式 VSR = VRR × (1 − Conditional ASR) を確認する関数も置く
- [x] Step 4.2: 有害判定を 2 通り実装する。主軸（FR1.3）は HarmBench Classifier 単独（`harmbench_cls_output == "Yes"`）。再現確認用（FR3.1）は `generate_flmsec_hyo.py` L81-88 と同じ OR 判定（HarmBench 分類器と各ベンチマーク分類器）。呼び出し側が判定方式を明示して選ぶ（既定を置かない）
- [x] Step 4.3: 4 ベンチマークの平均、特化 3 タスク（math、code、medical）の個別の値、補助の General 列、補助の正規化した総合値、seed 42〜44 の平均と標準偏差を計算する関数を書く。集計の仕方（平均の取り方、`None` の扱い）は、`generate_flmsec_hyo.py` L305-409 に合わせ、違う点があれば `v5/docs/survey_summary/definitions.md` に理由を書く。有用性 3 タスクは個別に返し、総合値は別の関数にして補助用であることを docstring に書く（FR1.4）
- [x] Step 4.4: `v5/tests/test_metrics.py` を書いて実行する。(a) 全件が妥当・有害 0 件、(b) 一部が無効（空、単語の重複、数字だけ）、(c) 全件が無効（VRR=0 で Conditional ASR が `None`）、(d) 同じデータで HarmBench 単独と OR 判定の値が違うこと、(e) 恒等式が成り立つこと、(f) 有用性の個別の値と補助の総合値が別々に返ること

### Step 5：比較ロジック層（FR1.2、FR1.5、FR4.1）

- [x] Step 5.1: `v5/src/v5lib/compare.py` を実装する。点は (手法, パターン, α) で、seed 平均と標準偏差を持つ。VRR の下限（主 80、感度分析 90 と 50。値は引数で受け、既定を置かない）で点をふるい、除外した点を一覧にして返す（FR1.2）
- [x] Step 5.2: 同じ場所に、厳密な Pareto 支配（Conditional ASR は低いほど良い、有用性は高いほど良い。どちらかが同じで、他方が良ければ支配）の判定を書く。補間はしない（FR1.5）。補助として、Conditional ASR の差が ±2.0 pt 以内の点どうしの近傍比較を書き、近傍内の有用性の差と、seed 間の標準偏差から見た不確実性（差が 1 標準偏差より小さいか）を返す
- [x] Step 5.3: 各ドメインの有用性を個別に比較し、結果を「観測事実」としてまとめる構造（`dict`）を返す。機構仮説と示唆はここでは作らない（FR5.1 の 3 段階のうち 1 段階目だけ）
- [x] Step 5.4: `v5/tests/test_compare.py` を書いて実行する。(a) VRR の下限でふるうこと（79.9 は落ち、80.0 は残る、感度分析の 3 値で結果が変わること）、(b) 厳密な Pareto 支配（支配される点、同点、非支配の点）、(c) 近傍比較の境界（差が 2.0 pt ちょうどは含む、2.01 は含まない）、(d) 点が 1 つだけのとき、(e) 全点が除外されたとき（空の結果を返し、例外にしない）

### Step 6：出力層（表と図。FR3.1〜FR3.5）

- [x] Step 6.1: `v5/src/v5lib/tables.py` と `v5/scripts/regen_flmsec_tables.py` を実装する。FLMSEC 論文の主な表（手法 × タスク、α=0.6 の主結果、`generate_flmsec_hyo.py` の列構成）を、HarmBench 単独と OR 判定の両方で作る。論文の表（`neurips_2026.tex` の表）の数値を読み取り、再現した値と比べる。比較の許容差は、論文の表示桁（小数 2 桁）の丸めに合わせて 0.005 とする。不一致は一覧にし、有害判定の違いによる差は別項目に分ける（FR3.1）。General 列は再現表に含める。出力は `v5/outputs/tables/`
- [x] Step 6.2: `v5/src/v5lib/plots.py` と `v5/scripts/plot_pareto_curves.py` を実装する。手法ごとの safety–utility 曲線（横軸 Conditional ASR、縦軸 有用性、点を α の順に結ぶ。補間はしない）を 4 パターン各 1 枚、計 4 枚で出す。単一ドメインの 3 パターンは対応するタスクだけをプロットする。`safety+math+code+medical` は特化 3 タスクを 3 つのサブプロットで 1 枚にする。VRR の下限を満たさない点は、除外した点として別の記号で示す。出力は `v5/outputs/figures/`（FR3.2）
- [x] Step 6.3: `v5/src/v5lib/ablation.py` と `v5/scripts/ablation_table.py` を実装する。`ablation/sst/` と `ablation/datafree/` の結果から、k × variant の表を作る。α、k、パターンなどの条件をそろえた列だけを同じ表に並べ、条件が違うセルを混ぜない。v3 に結果が無い条件は、別の条件で代用せず `N/A` とし、欠損の一覧（FR3.4）に理由と、探したファイル名のパターンを書く。α を動かした効果と、k・variant を動かした効果は、別の表にする（FR3.3）
- [x] Step 6.4: 出力ごとに、使った結果ファイルの一覧、データ件数、欠損、設定値を、同名の `.manifest.json`（または表の末尾の注記）として残す（FR3.4、NFR3）。乱数を使う箇所があれば seed を固定して記録する（NFR1）。同じ入力で 2 回実行し、出力が同じになることをテストで確認する
- [x] Step 6.5: `v5/tests/test_outputs.py` を書いて実行する。合成の結果ディレクトリで、(a) 表の再現と論文の値の比較（一致、不一致、判定差の別項目）、(b) 曲線が 4 枚できて、4 ドメインの図が 3 サブプロットであること、(c) アブレーション表の欠損が `N/A` で、代用されないこと、(d) manifest に入力パスと件数が入ること、(e) 同じ入力で 2 回実行して同じ出力になること（NFR1）

### Step 7：CPU 専用の検証層（FR2。V1〜V11）

- [x] Step 7.1: `v5/src/v5lib/hypotheses.py` に、各仮説の判定ロジックを実装する。入力は数値の辞書、出力は「支持」「不支持」「判定不能」のいずれかと根拠の数値。判定の指標と反証条件は、Step 8 の事前登録の値を設定ファイル（`v5/docs/survey_summary/preregistration.json`）から読み、コードに直接書かない（FR2.1、FR2.3）
- [x] Step 7.2: `v5/scripts/check_inputs.py` を実装する（FR2.2 の第 1 段階）。V1〜V11 に必要な入力（`v3/cache/fim/*.pt`、`v3/data/fim/*.json`、`v3/models/` の config と safetensors ヘッダ、`v3/results/vllm`）の有無とサイズを、読み取りだけで一覧にする。ファイルの中身は開かない
- [x] Step 7.3: `v5/scripts/check_v1_v9.py` を実装する（第 2 段階）。V1（FIM の 0 の割合）、V2（マスク比率と inf）、V3（マスクの Jaccard と順位相関）、V4（fp16 の丸め）、V5（注入量）、V6（系統）、V7（rope_theta）、V8（FIM データ）、V9（語彙）を、`code-quality-assessment.md` の確認方法のとおりに実装する。テンソルは 1 つずつ読み、全体をメモリに載せない（`torch.load(..., mmap=True, weights_only=True)`、safetensors は `safe_open` でテンソル単位）。FIM のキャッシュは大きいので、`--seed`、`--pattern`、`--layers`、`--max-tensors` で範囲を絞れるようにし、実行した範囲を出力に必ず記録する。範囲外は「判定不能」とし、「支持」「不支持」にしない。モデルの重みを開いて書き込まない。GPU を使わない（`device="cpu"` 固定、`cuda` が使えても使わない）
- [x] Step 7.4: `v5/scripts/check_v10_v11.py` を実装する（第 3 段階）。V10 は、ablation 結果のファイル名から、`k0.05`、`k0.1`、`additive`、`layerwise_*` の評価済みの条件を一覧にする。V11 は、Step 5 の比較ロジックを使い、SST と task_arithmetic を、観測済みの点の Pareto 支配と近傍比較で比べる
- [x] Step 7.5: V12〜V16（v1 に関する確認）は実装しない。必要なら、レポートで読解の補足として扱う（FR2.5）
- [x] Step 7.6: `v5/tests/test_hypotheses.py` を書いて実行する。合成の小さなテンソルで、(a) V1 の 0 の割合（fp16 で 0 に落ちる値を含むテンソル）、(b) V2 のマスク比率（λ の 0 が 80% 超だとマスクが全 1 になる）と inf の数、(c) V3 の Jaccard（同じ順位なら 1、無関係なら 0 に近い）、(d) V4 の ulp の判定、(e) 判定ロジックが「支持」「不支持」「判定不能」を、事前登録の閾値どおりに返すこと、(f) `--max-tensors` で範囲外になった仮説が「判定不能」になること、(g) 小さな `.pt` を `mmap` で読めること、(h) スクリプトが `v5/` の外に書かないこと

### Step 8：事前登録と定義の文書（FR1.1、FR1.2、FR2.1、FR2.2）

- [x] Step 8.1: `v5/docs/survey_summary/preregistration.md` と `preregistration.json` を作る。結果を見る前の記録として、次を書く（実行前に固定する。実データの結果を見てから書き換えない）。(1) 比較方法と採用基準を分けた定義（FR1.1）、(2) VRR の下限 80%（感度分析 90% と 50%）と、近傍比較の許容範囲 ±2.0 pt、依頼者が FLMSEC の表をすでに見ている事実（FR1.2）、(3) V1〜V11 の一覧（各 1 行：確認内容、判定の指標、反証条件）、(4) 判定の分類（支持、不支持、判定不能）と、「判定不能」にする条件（必要なデータが無い、実行範囲を絞った、要因を切り分けられない）、(5) 実行の順序（入力の確認、V1〜V9、V10〜V11）、(6) 正規化した総合値の計算方法（補助用）
- [x] Step 8.2: `v5/docs/survey_summary/definitions.md` を作る。VRR、Conditional ASR、VSR、ベンチマーク ASR の定義（FLMSEC 論文の行番号つき）、有害判定の主軸（HarmBench Classifier 単独）と OR 判定の違い、有用性の集計の仕方、`generate_flmsec_hyo.py` との違いを書く
- [x] Step 8.3: 事前登録の値を読むテスト（Step 7.6 の (e)）が、`preregistration.json` と同じ値を使っていることを確認する

### Step 9：実行の入口

- [x] Step 9.1: `v5/scripts/run_pipeline.py` を実装する。段階ごと（`inputs`、`v1_v9`、`v10_v11`、`tables`、`plots`、`ablation`）のコマンドを組み立てて表示するだけの `--dry-run`（既定）と、指定した段階だけを実行する `--execute --stages ...` を持つ。`--execute` は `--approved-by-user` が無いと拒否する（実行前に依頼者の許可を得る約束を、スクリプトの側でも確認する。FR2.4）。実行の記録（コマンド、開始と終了の時刻、終了コード）を `v5/outputs/logs/` に残す
- [x] Step 9.2: `v5/tests/test_pipeline.py` を書いて実行する。(a) `--dry-run` が何も書かずにコマンドを表示すること、(b) `--approved-by-user` なしの `--execute` が拒否されること

### Step 10：レポートの生成基盤（FR6、FR4.2、FR5.1）

- [x] Step 10.1: `v5/scripts/build_report.py` を実装する。`v5/outputs/` の表、図、manifest、仮説の判定を集めて、`v5/docs/survey_summary/report.md` の「結果の節」を組み立てる。固定の節（冒頭の定義、FR1.1）は `preregistration.md` から取り込み、数値は必ず元ファイルのパスつきで書く（NFR3）。考察（FR4）と設計案（FR5）の節は、Part B で、実行結果を見たうえで手書きし、この関数は上書きしない（`<!-- 手書き:` のマーカーで囲んだ範囲を保つ）
- [x] Step 10.2: `v5/tests/test_report.py` を書いて実行する。(a) 合成の出力から結果の節ができること、(b) 手書きのマーカー内を再生成で上書きしないこと、(c) 数値の行に元ファイルのパスが付くこと

### Step 11：ドキュメントとトレーサビリティ

- [x] Step 11.1: `v5/README.md` に、実行順序（`run_pipeline.py --dry-run` の出力の読み方、許可を得てから `--execute` を使うこと）、出力の場所、テストの実行コマンドを追記する
- [x] Step 11.2: `traceability.json` を `aidlc engine sensor-traceability --stage code-generation --output-path <この段階の記録フォルダ>/traceability.json --write-upstream` で作り、FR/NFR の各 ID に、実装または検証のファイルを対応させる（FR1.1 は `preregistration.md`、FR2.4 は `run_pipeline.py` など）。Part B で作る成果物（`report.md` の考察と設計案）に対応する ID（FR4、FR5）は、Part B が終わるまで `GAP` とし、終わったら `OK` にする

## Part B：実データでの実行と報告（依頼者の許可を得て、会話の中で行う）

ビルドを担当する開発者は、この Part を実行しない。Part A が終わった後、オーケストレーターが依頼者にコマンドを示し、許可を得てから実行する。

- [ ] Step B1: `run_pipeline.py --dry-run` の出力を依頼者に示し、段階ごとに実行の許可を得る（実行するコマンド、入力、出力先、予想される所要時間と、メモリの上限の目安を添える）
- [ ] Step B2: 第 1 段階（入力の確認）を実行し、V1〜V11 に必要な入力の有無を報告する。足りない入力に依存する仮説は、実行前に「判定不能の見込み」として依頼者に伝える
- [ ] Step B3: 第 2 段階（V1〜V9）を、範囲を絞って実行する（まず 1 seed、1 パターン、代表の層から。範囲は事前登録の範囲内で、実行前に依頼者に示す）。結果は、支持、不支持、判定不能に分類する
- [ ] Step B4: 第 3 段階（V10〜V11）と、表（FR3.1）、曲線（FR3.2）、アブレーション表（FR3.3）を実行する。FLMSEC の表との不一致の一覧を報告する
- [ ] Step B5: 実行結果を見たうえで、`report.md` の考察（FR4。FIM 選択、注入方式、ハイパーパラメータの 3 分類。各主張を観測事実、機構仮説、新手法への示唆の 3 段階に分ける）と、新しい merge 手法の設計案（FR5。文章と擬似コード。DLSP_hiromi2 に導入する設計と未検証の部分を分ける）を、手書きの節として書く
- [ ] Step B6: `traceability.json` の FR4、FR5 を `OK` に更新し、`code-summary.md` に、実行した範囲、実行していない範囲、判定不能の理由を書く

## Assumptions

None.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "test-after",
  "source": "org",
  "ordering": "implement each applicable testable layer, then write and run that layer's tests.",
  "scope": "poc",
  "test_strategy": "minimal",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop`, `classic` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    }
  ],
  "obligations": {
    "strategy": "minimal",
    "strategy_volume": [
      "One verifiable test per requirement at the narrowest effective level.",
      "At least one happy-path unit test per component.",
      "Unit tests are the default; a bugfix/security scope floor may require an integration or E2E regression when that is the narrowest level that reproduces the defect."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "test-after",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Data model / database behavior - implement.",
      "Data model / database behavior - write and run its tests after implementation.",
      "Repository / data access - implement.",
      "Repository / data access - write and run its tests after implementation.",
      "Business logic - implement.",
      "Business logic - write and run its tests after implementation.",
      "API / endpoint - implement.",
      "API / endpoint - write and run its tests after implementation.",
      "Frontend behavior - implement.",
      "Frontend behavior - write and run its tests after implementation.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:04b9b96625a5fdb1ca6669f4c5c779aaa2bc58912cd9db366657d591f9f98c84",
  "contract_sha256": "sha256:c039c687da4f6501d518118720bb16501c074a1cc249b5a2ccada81243a04a32"
}
```
