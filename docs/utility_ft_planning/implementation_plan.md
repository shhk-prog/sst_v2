# フルスケール評価ベンチマーク（全ドメイン・安全性）の実装計画

ユーザーのご要望に基づき、現在ごく一部（GSM8K, PubMedQA等）でのみ稼働している評価パイプラインを拡張し、**A〜Dのすべての公式ベンチマークを網羅的かつ自動で実行できるフルパイプライン**を実装します。

## 1. 目的と現状のギャップ
現在完了しているのは「A (lm-evaluation-harness)」の一部の動作確認パイプラインのみであり、数学の詳細タスク、GLUE全種、コーディング(B)、通信専門(C)、および安全性(D)の評価基盤が未実装です。これらすべてを追加実装します。

## 2. 実装計画詳細

### A. 一般推論・数学・GLUE・医学 (lm-evaluation-harness)
既存の `run_eval_all_utility.sh` を拡張します。
- **追加するタスク**: `math`, `math500`, `minerva_math`, `olympiadbench`, `collegemath`, `aime24`, `cola`, `mnli`, `qnli`, `qqp`, `rte`, `sst2`
- **課題**: `lm-evaluation-harness` にデフォルトで組み込まれていないタスク（例: `aime24`, `collegemath`）がある場合、公式のカスタムタスク用yaml設定ファイルを作成・配置して認識させます。

### B. コーディング (bigcode-evaluation-harness)
新たに `run_eval_coding.sh` を作成します。
- 既にclone済みの `bigcode-evaluation-harness` を使用。
- `mbpp`, `humaneval_pack`（または `humaneval`）を実行し、生成結果のPass@1などを算出する処理を実装します。

### C. 通信・専門ドメイン (TeleQnA)
新たに `run_eval_telecom.sh` を作成します。
- clone済みの `TeleQnA` リポジトリを利用。
- `TeleQnA`, `TeleData`, `TSpecLLM` ベンチマークスクリプトを呼び出し、モデルごとの正答率を出力するラッパーを作成します。

### D. Safety (安全性・アライメント)
新たに `run_eval_safety.sh` を作成します。
- `Llama-Guard-3-8B` を使用した **Red-teaming** 評価 (`DirectHarm`, `HexPhi`)
- `MD-Judge` (またはLLM-as-a-Judge) を用いた **安全性総合** 評価 (`HarmBench`, `SORRY-Bench`, `BeaverTails`)
- 各種有害プロンプトデータセットを入力し、出力結果を判定モデルにかける評価パイプラインをPythonスクリプトおよびシェルで構築します。

## 3. 全体統合
上記の各スクリプトを、単一の `RUN_ID` を渡すだけですべての評価（A〜D）を自動で並列/直列実行するマスタースクリプト `run_all_benchmarks.sh` に統合します。

## User Review Required

> [!IMPORTANT]  
> 大規模な拡張となるため、以下の点についてご確認ください。
> 1. **タスクのサポート状況**: `aime24` や `collegemath` など、一部の最新タスクは lm-eval 側に標準実装されていない場合があります。その場合、似た代替タスクにするか、あるいはスクレイピングしてカスタム定義を作るか、どちらの優先度が高いでしょうか？
> 2. **Llama-Guard / MD-Judge の重み**: DのSafety評価で判定に用いる `Llama-Guard-3-8B` 等のモデルは、HuggingFaceのアクセストークン（ゲート付きモデルの許可）が必要です。環境変数等に `HF_TOKEN` が設定されているという前提で進めてよろしいでしょうか？

上記の方針でよろしければ、順次スクリプトとパイプラインの構築を開始いたします。
