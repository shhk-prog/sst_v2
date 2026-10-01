# Base Modelの評価結果集計計画

`/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320` ディレクトリ内のBase Model評価結果ファイルをパース・抽出し、正確な一覧表を作成します。

## Proposed Changes

特に対象ソースコードの修正はありません。評価結果ファイルを検索・収集し、集計ドキュメントを作成します。

### 新規作成ドキュメント

#### [NEW] [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/summarize_base_models/task.md)
#### [NEW] [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/summarize_base_models/implementation_plan.md)
#### [NEW] [walkthrough.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/summarize_base_models/walkthrough.md)

## Verification Plan

### Manual Verification
- `grep_search` や `view_file` を用いて、各モデル・各タスクのJSONファイルからスコアを漏れなく抽出します。
- 抽出した値とJSONファイルの実値が一致しているか、いくつかのサンプルを突き合わせて検証します。
