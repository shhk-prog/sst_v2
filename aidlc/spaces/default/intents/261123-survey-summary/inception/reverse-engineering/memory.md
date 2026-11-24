<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-23T12:17:39Z — SAGAI_EN_sst の付録の Data-Free（|W| を両側に使用、L1142-1144）は比 λ̂ がほぼ一定になり、選択が大きさの順位だけになると解釈した。本文の Δ² 版（L747-761）とコードは一致する。
- 2026-11-23T12:17:39Z — DLSP_hiromi2 = SAGAI_EN_sst の `\cite{11050841}`（2025 IEEE SPW）であることを main.bib L51-59 とタイトルの一致で確認し、「書誌の照合はしていない」の記述を置き換えた。
- 2026-11-23T12:47:48Z — 前回の Data-Free の解釈（比が一定）は誤りだった。v1 の `sst_merge_data_free.py` L29-69, L246-251 が Utility と Safety の LoRA 重みの二乗を別々に求めて比を取ると確認し、architecture.md と code-quality-assessment.md を訂正した（付録の |W| は表記の曖昧さ）。
- 2026-11-23T12:47:48Z — 論文の数値の出所は v1。代表セル 7 件（TA α=0.3、Interpolation k=20% α=0.6、k=50% α=1.0、Additive soft、Additive hard k=5%）が v1 の結果 JSON と一致し、k=5% Interpolation は 2 つのフォルダ（`interpolation/` と ` A7-7ep/`）の混在と分かった。
- 2026-11-23T12:47:48Z — 論文の TA の数値は v1 の「GEVP 無効の補間」と同じモデルの結果（rouge1 が 16 桁まで一致）と解釈した。TA = (1−α)u + αs の式が同じなので整合する。
- 2026-11-23T12:47:48Z — 仮説: 論文の A5 Data-Free k=10%/20% の表が同一なのは貼り間違いではなく、k が命名だけだった旧ドライバの run が結果に残ったため（`run_data_free_merge.py` L50 のコメントと旧ラベルの結果が根拠。新旧の更新日時は未確認）。

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-23T08:50:00Z — 全体スキャンではなく focused scan（kind: partial）にした; v3 は 15T 規模で baselines 配下にモデル重みがあり、スナップショットが ENOMEM で失敗したため、コード・設定・論文に限定。results/vllm は shallow のみ。
- 2026-11-23T08:50:00Z — 開発者の handoff がステージ試行の再開始より前に書かれていたため、内容を変えずに開発者自身に再保存させてからリンクを記録した。
- 2026-11-23T12:47:48Z — v1 / v2 はリポジトリ外のため `analyzed.paths` にも `shallow.paths` にも入れず、components 名（v1-*, v2-*）だけ追加した。ブリーフの許可どおり、読むだけで実行はしていない。
- 2026-11-23T12:47:48Z — 貼り付けメモ 1 の列挙ファイルのうち `run_sst_merge_comparison.sh` と `run_all_experiments.sh` は論文の数値の生成元ではないと判断した（前者は FIM なしの単発、後者は存在しないパスを呼ぶ）。実際の掃引ドライバは `v1/scripts/merging/` にある。

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-23T12:47:48Z — v1 の結果は代表セルだけ読み、全セルの突き合わせはしなかった（時間と読む範囲の制約）。その分、k=5% 以外の Interpolation の列、Data-Free の新ラベルの表は未照合として V14・V15 に回した。
- 2026-11-23T12:47:48Z — 4 者照合の表は 1 つにまとめず、メモ 1〜7 の判定表、手順ごとの照合表、代表セル照合表の 3 つに分けた（Minimal でも読み手が主張ごとに辿れるようにするため）。

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-23T08:50:00Z — 未検証の仮説：FIM の fp16 で値が 0 に潰れ SST が task_arithmetic に退化している可能性、code/medical モデルの派生元が Llama-2-7b-hf でない可能性。cache/fim/*.pt と各モデル config.json で確認が必要（GPU 不要）。
- 2026-11-23T12:17:39Z — SAGAI_EN_sst の数値（Llama-3.1-8B、A5/A6/A7 LoRA）を出したコードの所在は v3 内で見つからない。論文のベース名（本文 meta-llama-3.1-8b、付録 -Instruct）がどちらか正しいかは研究者への確認が必要。（2026-11-23T12:47:48Z 追記: 所在は v1、ベースは Llama-3.1-8B-Instruct で解消）
- 2026-11-23T12:47:48Z — v1 の FIM でアダプターがモデルに載る処理に疑い（`_load_adapter_to_model` は鍵の末尾 3 要素だけで照合しレイヤー番号を含まない。`run_all_merges_hard.py` L387, L402 の条件は標準の PEFT 鍵形式だと成立しない可能性）。アダプターの実体と実行ログが無く未確認（V12）。論文の数値への影響は不明。
- 2026-11-23T12:47:48Z — 論文の各セルがどの A7（3/5/7/10 epoch）のアダプターから作られたか不明（` A7-7ep/` と `interpolation/` で k=5% α=0.7 が 86.8% と 88.4% に分かれる）。研究者への確認が必要（V14）。
- 2026-11-23T12:47:48Z — A5/A6 の評価データ（`repliqa_0` / Alpaca `train` の先頭 500 件）が学習データと同じ split。分割の有無は未確認（V16）。研究者への確認が必要。
- 2026-11-23T12:47:48Z — 論文の DARE の説明（τ_s だけを疎にする）と v1 のコード（両方を疎にする）が不一致。論文の誤記か別実装かは研究者への確認が必要。
